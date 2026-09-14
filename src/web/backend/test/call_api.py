from time import monotonic, sleep
from typing import Any

import requests
import urllib3
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from web.backend.config.nifi_config import get_nifi_parameter_token, get_nifi_url


app = FastAPI()

# NiFi trong docker-compose đang dùng chứng chỉ HTTPS tự ký.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NIFI_TIMEOUT_SECONDS = 30
PROCESSOR_STOP_TIMEOUT_SECONDS = 30


class UpdateProcessorPropertiesRequest(BaseModel):
    process_group_id: str = Field(
        ...,
        description="ID của process group chứa processor",
    )
    processor_id: str = Field(
        ...,
        description="ID của processor được chọn để cập nhật",
    )
    properties: dict[str, str | None] = Field(
        ...,
        description="Các property cần thay đổi; dùng null để xóa giá trị",
    )


class UpdateProcessorSchedulingRequest(BaseModel):
    schedulingStrategy: str | None = Field(
        None,
        description="Ví dụ: TIMER_DRIVEN hoặc CRON_DRIVEN",
    )
    schedulingPeriod: str | None = Field(
        None,
        description="Ví dụ: 1 min, 30 sec hoặc biểu thức CRON",
    )
    concurrentlySchedulableTaskCount: int | None = Field(None, ge=1)
    executionNode: str | None = Field(
        None,
        description="Ví dụ: ALL hoặc PRIMARY",
    )
    runDurationMillis: int | None = Field(None, ge=0)
    yieldDuration: str | None = None
    penaltyDuration: str | None = None
    restartAfterUpdate: bool = Field(
        True,
        description="Khởi động lại nếu processor đang RUNNING trước khi cập nhật",
    )


def _nifi_error_detail(response: requests.Response) -> Any:
    """Đọc lỗi JSON của NiFi nếu có, nếu không trả về nội dung text."""
    try:
        return response.json()
    except ValueError:
        return response.text or "NiFi returned an empty response"


def _raise_for_nifi_error(response: requests.Response) -> None:
    if not response.ok:
        raise HTTPException(
            status_code=response.status_code,
            detail=_nifi_error_detail(response),
        )


def _get_nifi_access_token() -> str:
    response = requests.post(
        f"{get_nifi_url()}/access/token",
        data=get_nifi_parameter_token(),
        verify=False,
        timeout=NIFI_TIMEOUT_SECONDS,
    )
    _raise_for_nifi_error(response)
    return response.text


def _authorization_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


def _get_processor(
    nifi_url: str,
    processor_id: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    response = requests.get(
        f"{nifi_url}/processors/{processor_id}",
        headers=headers,
        verify=False,
        timeout=NIFI_TIMEOUT_SECONDS,
    )
    _raise_for_nifi_error(response)
    return response.json()


def _revision_payload(processor_entity: dict[str, Any]) -> dict[str, Any]:
    revision = processor_entity.get("revision")
    if not revision or revision.get("version") is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="NiFi response does not contain the processor revision",
        )

    return {
        "version": revision["version"],
        **(
            {"clientId": revision["clientId"]}
            if revision.get("clientId")
            else {}
        ),
    }


def _set_processor_run_status(
    nifi_url: str,
    processor_id: str,
    processor_entity: dict[str, Any],
    new_state: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    response = requests.put(
        f"{nifi_url}/processors/{processor_id}/run-status",
        headers={**headers, "Content-Type": "application/json"},
        json={
            "revision": _revision_payload(processor_entity),
            "state": new_state,
        },
        verify=False,
        timeout=NIFI_TIMEOUT_SECONDS,
    )
    _raise_for_nifi_error(response)
    return response.json()


def _wait_until_processor_stopped(
    nifi_url: str,
    processor_id: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    deadline = monotonic() + PROCESSOR_STOP_TIMEOUT_SECONDS
    while monotonic() < deadline:
        processor_entity = _get_processor(nifi_url, processor_id, headers)
        component = processor_entity.get("component", {})
        if (
            component.get("state") == "STOPPED"
            and component.get("physicalState", "STOPPED") == "STOPPED"
        ):
            return processor_entity
        sleep(0.5)

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Processor did not stop before the 30-second timeout",
    )


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/nifi/login")
def nifi_login():
    try:
        return {"token": _get_nifi_access_token()}
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to NiFi: {exc}",
        ) from exc


@app.get("/nifi/processors/{processor_id}/scheduling")
def get_processor_scheduling(processor_id: str):
    """Lấy cấu hình scheduling hiện tại của một processor."""
    try:
        token = _get_nifi_access_token()
        response = requests.get(
            f"{get_nifi_url()}/processors/{processor_id}",
            headers=_authorization_headers(token),
            verify=False,
            timeout=NIFI_TIMEOUT_SECONDS,
        )
        _raise_for_nifi_error(response)

        processor_entity = response.json()
        component = processor_entity.get("component", {})
        config = component.get("config", {})

        return {
            "processorId": component.get("id", processor_id),
            "processorName": component.get("name"),
            "state": component.get("state"),
            "scheduling": {
                "schedulingStrategy": config.get("schedulingStrategy"),
                "schedulingPeriod": config.get("schedulingPeriod"),
                "concurrentlySchedulableTaskCount": config.get(
                    "concurrentlySchedulableTaskCount"
                ),
                "executionNode": config.get("executionNode"),
                "runDurationMillis": config.get("runDurationMillis"),
                "yieldDuration": config.get("yieldDuration"),
                "penaltyDuration": config.get("penaltyDuration"),
            },
            "revision": processor_entity.get("revision"),
        }
    except HTTPException:
        raise
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate with NiFi: {exc}",
        ) from exc


@app.put("/nifi/processors/{processor_id}/scheduling")
def update_processor_scheduling(
    processor_id: str,
    request_body: UpdateProcessorSchedulingRequest,
):
    """Cập nhật scheduling trên NiFi và giữ lại trạng thái chạy ban đầu."""
    scheduling_fields = (
        "schedulingStrategy",
        "schedulingPeriod",
        "concurrentlySchedulableTaskCount",
        "executionNode",
        "runDurationMillis",
        "yieldDuration",
        "penaltyDuration",
    )
    scheduling_config = {
        field_name: getattr(request_body, field_name)
        for field_name in scheduling_fields
        if getattr(request_body, field_name) is not None
    }
    if not scheduling_config:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one scheduling parameter to update",
        )

    nifi_url = get_nifi_url()

    try:
        token = _get_nifi_access_token()
        headers = _authorization_headers(token)
        processor_entity = _get_processor(nifi_url, processor_id, headers)
        component = processor_entity.get("component", {})
        original_state = component.get("state")

        if original_state in {"STARTING", "STOPPING", "RUN_ONCE"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Processor is currently {original_state}; wait for the state "
                    "transition to finish before updating scheduling"
                ),
            )

        stopped_by_api = original_state == "RUNNING"
        if stopped_by_api:
            _set_processor_run_status(
                nifi_url,
                processor_id,
                processor_entity,
                "STOPPED",
                headers,
            )
            processor_entity = _wait_until_processor_stopped(
                nifi_url,
                processor_id,
                headers,
            )

        update_response = requests.put(
            f"{nifi_url}/processors/{processor_id}",
            headers={**headers, "Content-Type": "application/json"},
            json={
                "id": processor_id,
                "revision": _revision_payload(processor_entity),
                "component": {
                    "id": processor_id,
                    "config": scheduling_config,
                },
            },
            verify=False,
            timeout=NIFI_TIMEOUT_SECONDS,
        )
        _raise_for_nifi_error(update_response)
        updated_processor = update_response.json()

        final_processor = updated_processor
        restarted = False
        if stopped_by_api and request_body.restartAfterUpdate:
            final_processor = _set_processor_run_status(
                nifi_url,
                processor_id,
                updated_processor,
                "RUNNING",
                headers,
            )
            restarted = True

        final_component = final_processor.get("component", {})
        final_config = final_component.get("config", {})

        return {
            "message": "Processor scheduling updated on NiFi successfully",
            "processorId": final_component.get("id", processor_id),
            "processorName": final_component.get("name"),
            "originalState": original_state,
            "state": final_component.get("state"),
            "restarted": restarted,
            "scheduling": {
                field_name: final_config.get(field_name)
                for field_name in scheduling_fields
            },
            "revision": final_processor.get("revision"),
        }
    except HTTPException:
        raise
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate with NiFi: {exc}",
        ) from exc


@app.post("/nifi/processors/properties")
def update_processor_properties(request_body: UpdateProcessorPropertiesRequest):
    """Chọn processor trong process group và cập nhật các property của nó."""
    if not request_body.properties:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="properties must contain at least one item",
        )

    nifi_url = get_nifi_url()

    try:
        token = _get_nifi_access_token()
        headers = _authorization_headers(token)

        # Lấy các processor thuộc process group để kiểm tra lựa chọn của client.
        processors_response = requests.get(
            f"{nifi_url}/process-groups/{request_body.process_group_id}/processors",
            headers=headers,
            params={"includeDescendantGroups": "false"},
            verify=False,
            timeout=NIFI_TIMEOUT_SECONDS,
        )
        _raise_for_nifi_error(processors_response)

        processor_entities = processors_response.json().get("processors", [])
        selected_processor = next(
            (
                processor
                for processor in processor_entities
                if processor.get("id") == request_body.processor_id
                or processor.get("component", {}).get("id")
                == request_body.processor_id
            ),
            None,
        )

        if selected_processor is None:
            available_processors = [
                {
                    "id": processor.get("id")
                    or processor.get("component", {}).get("id"),
                    "name": processor.get("component", {}).get("name"),
                }
                for processor in processor_entities
            ]
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Processor does not belong to the process group",
                    "availableProcessors": available_processors,
                },
            )

        # Lấy revision mới nhất ngay trước khi PUT để hạn chế lỗi 409.
        processor_response = requests.get(
            f"{nifi_url}/processors/{request_body.processor_id}",
            headers=headers,
            verify=False,
            timeout=NIFI_TIMEOUT_SECONDS,
        )
        _raise_for_nifi_error(processor_response)
        processor_entity = processor_response.json()

        revision = processor_entity.get("revision")
        if not revision or revision.get("version") is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="NiFi response does not contain the processor revision",
            )

        update_payload = {
            "id": request_body.processor_id,
            "revision": {
                "version": revision["version"],
                **(
                    {"clientId": revision["clientId"]}
                    if revision.get("clientId")
                    else {}
                ),
            },
            "component": {
                "id": request_body.processor_id,
                "config": {"properties": request_body.properties},
            },
        }

        update_response = requests.put(
            f"{nifi_url}/processors/{request_body.processor_id}",
            headers={**headers, "Content-Type": "application/json"},
            json=update_payload,
            verify=False,
            timeout=NIFI_TIMEOUT_SECONDS,
        )
        _raise_for_nifi_error(update_response)
        updated_processor = update_response.json()
        component = updated_processor.get("component", {})

        return {
            "message": "Processor properties updated successfully",
            "processGroupId": request_body.process_group_id,
            "processor": {
                "id": component.get("id", request_body.processor_id),
                "name": component.get("name"),
                "state": component.get("state"),
                "properties": component.get("config", {}).get("properties", {}),
            },
            "revision": updated_processor.get("revision"),
        }
    except HTTPException:
        raise
    except (requests.RequestException, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate with NiFi: {exc}",
        ) from exc
