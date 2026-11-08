-- Repository metric trends.
-- Table: `repopulse.repository_snapshots`, loaded from repository_snapshots.csv.
-- Replace PROJECT_ID with your own BigQuery Sandbox project.

-- 1. Latest metrics per repository.
WITH ranked AS (
  SELECT
    repository_full_name,
    stars_count,
    forks_count,
    open_issues_count,
    watchers_count,
    captured_at,
    ROW_NUMBER() OVER (
      PARTITION BY repository_full_name ORDER BY captured_at DESC
    ) AS recency
  FROM `PROJECT_ID.repopulse.repository_snapshots`
)
SELECT
  repository_full_name,
  stars_count,
  forks_count,
  open_issues_count,
  watchers_count,
  captured_at AS last_captured_at
FROM ranked
WHERE recency = 1
ORDER BY stars_count DESC;


-- 2. Star and fork growth between the earliest and latest snapshot.
WITH bounds AS (
  SELECT
    repository_full_name,
    MIN(captured_at) AS first_captured_at,
    MAX(captured_at) AS last_captured_at,
    COUNT(*) AS snapshot_count
  FROM `PROJECT_ID.repopulse.repository_snapshots`
  GROUP BY repository_full_name
),
first_values AS (
  SELECT
    s.repository_full_name,
    s.stars_count AS first_stars,
    s.forks_count AS first_forks
  FROM `PROJECT_ID.repopulse.repository_snapshots` AS s
  JOIN bounds AS b
    ON b.repository_full_name = s.repository_full_name
   AND b.first_captured_at = s.captured_at
),
last_values AS (
  SELECT
    s.repository_full_name,
    s.stars_count AS last_stars,
    s.forks_count AS last_forks
  FROM `PROJECT_ID.repopulse.repository_snapshots` AS s
  JOIN bounds AS b
    ON b.repository_full_name = s.repository_full_name
   AND b.last_captured_at = s.captured_at
)
SELECT
  b.repository_full_name,
  b.snapshot_count,
  b.first_captured_at,
  b.last_captured_at,
  f.first_stars,
  l.last_stars,
  l.last_stars - f.first_stars AS stars_gained,
  l.last_forks - f.first_forks AS forks_gained,
  SAFE_DIVIDE(l.last_stars - f.first_stars, NULLIF(f.first_stars, 0)) * 100
    AS stars_growth_percent
FROM bounds AS b
JOIN first_values AS f USING (repository_full_name)
JOIN last_values AS l USING (repository_full_name)
WHERE b.snapshot_count > 1
ORDER BY stars_gained DESC;


-- 3. Top repositories by star count, with their daily star rate.
WITH bounds AS (
  SELECT
    repository_full_name,
    MIN(captured_at) AS first_captured_at,
    MAX(captured_at) AS last_captured_at,
    MIN(stars_count) AS min_stars,
    MAX(stars_count) AS max_stars
  FROM `PROJECT_ID.repopulse.repository_snapshots`
  GROUP BY repository_full_name
)
SELECT
  repository_full_name,
  max_stars AS stars_count,
  TIMESTAMP_DIFF(last_captured_at, first_captured_at, DAY) AS tracked_days,
  SAFE_DIVIDE(
    max_stars - min_stars,
    NULLIF(TIMESTAMP_DIFF(last_captured_at, first_captured_at, DAY), 0)
  ) AS stars_per_day
FROM bounds
ORDER BY stars_count DESC
LIMIT 20;


-- 4. Daily snapshot coverage, to spot gaps in the manually synced history.
SELECT
  DATE(captured_at) AS captured_on,
  COUNT(DISTINCT repository_full_name) AS repositories_synced,
  COUNT(*) AS snapshots
FROM `PROJECT_ID.repopulse.repository_snapshots`
GROUP BY captured_on
ORDER BY captured_on DESC;
