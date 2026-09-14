CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE nifi_process_group (
    id BIGSERIAL PRIMARY KEY,
    group_id VARCHAR(255) UNIQUE NOT NULL,
    group_name VARCHAR(255) NOT NULL,
    parent_id INTEGER,
    level INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_process_group_parent
        FOREIGN KEY (parent_id)
        REFERENCES nifi_process_group(id)
        ON DELETE SET NULL
);

CREATE TABLE nifi_source (
    id BIGSERIAL PRIMARY KEY,
    source_id VARCHAR(255) UNIQUE NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    process_group_id INTEGER NOT NULL,
    vendor VARCHAR(255),
    remote_path TEXT,
	schedule_start TIMESTAMP,
	schedule_end TIMESTAMP,
    status VARCHAR(100),

    CONSTRAINT fk_source_process_group
        FOREIGN KEY (process_group_id)
        REFERENCES nifi_process_group(id)
        ON DELETE CASCADE
);

CREATE TABLE nifi_component (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL,
    component_id TEXT NOT NULL UNIQUE,
    component_name TEXT,
    component_type TEXT NOT NULL,
    processor_type TEXT,
    source_component_id TEXT,
    destination_component_id TEXT,
    concurrent_tasks INTEGER,
    status TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,

    CONSTRAINT fk_nifi_component_source
        FOREIGN KEY (source_id)
        REFERENCES nifi_source(id)
);

CREATE TABLE download_request (
    id BIGSERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    source_id BIGINT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failure_reason TEXT,

    CONSTRAINT fk_download_request_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id),

    CONSTRAINT fk_download_request_source
        FOREIGN KEY (source_id)
        REFERENCES nifi_source(id)
);

CREATE TABLE metric_history (
    source_id BIGINT NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    queued_count BIGINT,
    queue_bytes BIGINT,
    input_file_rate DOUBLE PRECISION,
    input_byte_rate DOUBLE PRECISION,
    processed_file_rate DOUBLE PRECISION,
    processed_byte_rate DOUBLE PRECISION,
    concurrent_tasks INTEGER,

    CONSTRAINT pk_metric_history
        PRIMARY KEY (source_id, recorded_at),

    CONSTRAINT fk_metric_history_source
        FOREIGN KEY (source_id)
        REFERENCES nifi_source(id)
);

CREATE TABLE allocation_history (
    id BIGINT NOT NULL,
    source_id BIGINT NOT NULL,
    request_id BIGINT,
    old_concurrent_tasks INTEGER NOT NULL,
    new_concurrent_tasks INTEGER NOT NULL,
    reason TEXT,
    queued_count BIGINT,
    queue_bytes BIGINT,
    input_file_rate DOUBLE PRECISION,
    input_byte_rate DOUBLE PRECISION,
    processed_file_rate DOUBLE PRECISION,
    processed_byte_rate DOUBLE PRECISION,
    created_at TIMESTAMP NOT NULL,

    CONSTRAINT pk_allocation_history
        PRIMARY KEY (id, created_at),

    CONSTRAINT fk_allocation_history_source
        FOREIGN KEY (source_id)
        REFERENCES nifi_source(id),

    CONSTRAINT fk_allocation_history_request
        FOREIGN KEY (request_id)
        REFERENCES download_request(id)
);

CREATE EXTENSION IF NOT EXISTS timescaledb;

SELECT create_hypertable(
    'metric_history',
    'recorded_at',
	chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

SELECT create_hypertable(
    'allocation_history',
    'created_at',
	chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);