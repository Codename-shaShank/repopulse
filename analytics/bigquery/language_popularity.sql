-- Language composition across tracked repositories.
-- Table: `repopulse.language_stats`, loaded from language_stats.csv.
-- Replace PROJECT_ID with your own BigQuery Sandbox project.

-- 1. Most common languages, counted once per repository using its latest snapshot.
WITH latest_snapshot AS (
  SELECT
    repository_full_name,
    MAX(captured_at) AS captured_at
  FROM `PROJECT_ID.repopulse.language_stats`
  GROUP BY repository_full_name
),
latest_languages AS (
  SELECT ls.*
  FROM `PROJECT_ID.repopulse.language_stats` AS ls
  JOIN latest_snapshot AS s
    ON s.repository_full_name = ls.repository_full_name
   AND s.captured_at = ls.captured_at
)
SELECT
  language,
  COUNT(DISTINCT repository_full_name) AS repositories_using,
  SUM(bytes_of_code) AS total_bytes
FROM latest_languages
GROUP BY language
ORDER BY repositories_using DESC, total_bytes DESC;


-- 2. Language byte totals and share within each repository, latest snapshot only.
WITH latest_snapshot AS (
  SELECT
    repository_full_name,
    MAX(captured_at) AS captured_at
  FROM `PROJECT_ID.repopulse.language_stats`
  GROUP BY repository_full_name
),
latest_languages AS (
  SELECT ls.*
  FROM `PROJECT_ID.repopulse.language_stats` AS ls
  JOIN latest_snapshot AS s
    ON s.repository_full_name = ls.repository_full_name
   AND s.captured_at = ls.captured_at
)
SELECT
  repository_full_name,
  language,
  bytes_of_code,
  ROUND(
    SAFE_DIVIDE(
      bytes_of_code,
      SUM(bytes_of_code) OVER (PARTITION BY repository_full_name)
    ) * 100,
    2
  ) AS share_percent
FROM latest_languages
ORDER BY repository_full_name, bytes_of_code DESC;


-- 3. The dominant language of each repository.
WITH latest_snapshot AS (
  SELECT
    repository_full_name,
    MAX(captured_at) AS captured_at
  FROM `PROJECT_ID.repopulse.language_stats`
  GROUP BY repository_full_name
),
ranked AS (
  SELECT
    ls.repository_full_name,
    ls.language,
    ls.bytes_of_code,
    ROW_NUMBER() OVER (
      PARTITION BY ls.repository_full_name ORDER BY ls.bytes_of_code DESC
    ) AS position
  FROM `PROJECT_ID.repopulse.language_stats` AS ls
  JOIN latest_snapshot AS s
    ON s.repository_full_name = ls.repository_full_name
   AND s.captured_at = ls.captured_at
)
SELECT repository_full_name, language AS dominant_language, bytes_of_code
FROM ranked
WHERE position = 1
ORDER BY bytes_of_code DESC;


-- 4. How a repository's language mix shifted between its first and last snapshot.
WITH bounds AS (
  SELECT
    repository_full_name,
    MIN(captured_at) AS first_captured_at,
    MAX(captured_at) AS last_captured_at
  FROM `PROJECT_ID.repopulse.language_stats`
  GROUP BY repository_full_name
)
SELECT
  b.repository_full_name,
  COALESCE(first_mix.language, last_mix.language) AS language,
  COALESCE(first_mix.bytes_of_code, 0) AS first_bytes,
  COALESCE(last_mix.bytes_of_code, 0) AS last_bytes,
  COALESCE(last_mix.bytes_of_code, 0) - COALESCE(first_mix.bytes_of_code, 0)
    AS bytes_change
FROM bounds AS b
LEFT JOIN `PROJECT_ID.repopulse.language_stats` AS first_mix
  ON first_mix.repository_full_name = b.repository_full_name
 AND first_mix.captured_at = b.first_captured_at
FULL OUTER JOIN `PROJECT_ID.repopulse.language_stats` AS last_mix
  ON last_mix.repository_full_name = b.repository_full_name
 AND last_mix.captured_at = b.last_captured_at
 AND last_mix.language = first_mix.language
WHERE b.first_captured_at < b.last_captured_at
ORDER BY b.repository_full_name, bytes_change DESC;
