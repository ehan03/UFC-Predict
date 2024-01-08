"""This is just a placeholder file"""

PRELIMINARY_MATCHING_QUERY = """
WITH cte1 AS (
  SELECT 
    MIN(fighter_id) AS fighter_id, 
    fighter_name 
  FROM 
    UFCSTATS_FIGHTERS 
  GROUP BY 
    fighter_name 
  HAVING 
    COUNT(fighter_name) = 1
), 
cte2 AS (
  SELECT 
    MIN(fighter_slug) AS fighter_slug, 
    fighter_name 
  FROM 
    FIGHTODDSIO_FIGHTERS 
  GROUP BY 
    fighter_name 
  HAVING 
    COUNT(fighter_name) = 1
)
SELECT 
  t2.fighter_slug, 
  t1.fighter_id 
FROM 
  UFCSTATS_FIGHTERS AS t1 
  INNER JOIN FIGHTODDSIO_FIGHTERS AS t2 ON (
    t1.fighter_name = t2.fighter_name 
    AND t1.fighter_nickname = t2.fighter_nickname
  )
UNION 
SELECT 
  t2.fighter_slug, 
  t1.fighter_id 
FROM 
  UFCSTATS_FIGHTERS AS t1 
  INNER JOIN FIGHTODDSIO_FIGHTERS AS t2 ON (
    t1.fighter_name = t2.fighter_name 
    AND t1.date_of_birth = t2.date_of_birth
  )
UNION 
SELECT 
  t2.fighter_slug, 
  t1.fighter_id 
FROM 
  UFCSTATS_FIGHTERS AS t1 
  INNER JOIN FIGHTODDSIO_FIGHTERS AS t2 ON (
    t1.fighter_nickname = t2.fighter_nickname 
    AND t1.date_of_birth = t2.date_of_birth
  )
UNION 
SELECT 
  t2.fighter_slug, 
  t1.fighter_id 
FROM 
  cte1 AS t1 
  INNER JOIN cte2 AS t2 ON (
    t1.fighter_name = t2.fighter_name
  );
"""
