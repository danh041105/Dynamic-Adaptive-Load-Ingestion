
CREATE ROWSTORE REFERENCE TABLE users (
    user_id BIGINT NOT NULL AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (user_id),
    UNIQUE KEY uk_users_username (username)
);

CREATE ROWSTORE REFERENCE TABLE nifi_process_group (
    id BIGINT NOT NULL AUTO_INCREMENT,
    group_id VARCHAR(100) NOT NULL,
    group_name VARCHAR(255) NOT NULL,
    parent_id BIGINT NULL,
    level INT NULL,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_nifi_process_group_group_id (group_id),
    KEY idx_nifi_process_group_parent_id (parent_id)
);

CREATE ROWSTORE REFERENCE TABLE nifi_source (
    id BIGINT NOT NULL AUTO_INCREMENT,
    source_id VARCHAR(100) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    process_group_id BIGINT NOT NULL,
    vendor VARCHAR(100) NULL,
    remote_path VARCHAR(1000) NULL,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_nifi_source_source_id (source_id),
    KEY idx_nifi_source_process_group_id (process_group_id)
);

CREATE ROWSTORE REFERENCE TABLE nifi_component (
    id BIGINT NOT NULL AUTO_INCREMENT,
    source_id BIGINT NOT NULL,
    component_id VARCHAR(100) NOT NULL,
    component_name VARCHAR(255) NOT NULL,
    component_type VARCHAR(50) NOT NULL,
    destination_component_id VARCHAR(100) NULL,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_nifi_component_component_id (component_id),
    KEY idx_nifi_component_source_id (source_id)
);

CREATE ROWSTORE TABLE download_request (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    source_id BIGINT NOT NULL,
    start_time DATETIME(6) NOT NULL,
    end_time DATETIME(6) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    started_at DATETIME(6) NULL,
    completed_at DATETIME(6) NULL,
    failure_reason VARCHAR(1000) NULL,
    PRIMARY KEY (id),
    KEY idx_download_request_user_id (user_id),
    KEY idx_download_request_source_id (source_id),
    KEY idx_download_request_status (status)
);

CREATE TABLE metric_history (
    source_id BIGINT NOT NULL,
    recorded_at DATETIME(6) NOT NULL SERIES TIMESTAMP,
    queued_count BIGINT NULL,
    queue_bytes BIGINT NULL,
    input_files DOUBLE NULL,
    avg_input_bytes DOUBLE NULL,
    processed_files DOUBLE NULL,
    processed_bytes DOUBLE NULL,
    concurrent_tasks INT NULL,
    PRIMARY KEY (source_id, recorded_at),
    SHARD KEY (source_id),
    SORT KEY (source_id, recorded_at)
);

CREATE TABLE allocation_history (
    id BIGINT NOT NULL AUTO_INCREMENT,
    source_id BIGINT NOT NULL,
    request_id BIGINT NULL,
    old_concurrent_tasks INT NOT NULL,
    new_concurrent_tasks INT NOT NULL,
    reason VARCHAR(255) NULL,
    queued_count BIGINT NULL,
    queue_bytes BIGINT NULL,
    input_files DOUBLE NULL,
    avg_input_bytes DOUBLE NULL,
    processed_files DOUBLE NULL,
    processed_bytes DOUBLE NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) SERIES TIMESTAMP,
    PRIMARY KEY (id),
    SORT KEY (created_at),
    KEY idx_allocation_source_id (source_id),
    KEY idx_allocation_request_id (request_id)
);