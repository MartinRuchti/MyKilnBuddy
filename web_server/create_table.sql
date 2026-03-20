CREATE TABLE datapoints (
  tempid bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  measured_at timestamptz NOT NULL DEFAULT now(),
  temperature integer NOT NULL
);
CREATE INDEX ON temperature_readings (measured_at);