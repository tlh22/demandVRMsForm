-- survey areas
--DROP TABLE IF EXISTS mhtc_operations."SurveyAreas";
CREATE TABLE mhtc_operations."SurveyAreas"
(
    id SERIAL,
    name character varying(32) COLLATE pg_catalog."default",
    geom geometry(MultiPolygon,27700),
    CONSTRAINT "SurveyAreas_pkey" PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE mhtc_operations."SurveyAreas"
    OWNER to postgres;

ALTER TABLE "mhtc_operations"."RC_Sections_merged"
    ADD COLUMN "SurveyArea" integer;


--

UPDATE "mhtc_operations"."RC_Sections_merged" AS s
SET "SurveyArea" = a."Code"
FROM mhtc_operations."SurveyAreas" a
WHERE ST_WITHIN (s.geom, a.geom);

--
-- Calculate length of section within area

SELECT a."SurveyAreaName", SUM(s."SectionLength")
FROM mhtc_operations."RC_Sections_merged" s, mhtc_operations."SurveyAreas" a
WHERE ST_WITHIN (s.geom, a.geom)
GROUP BY a."SurveyAreaName"
ORDER BY a."SurveyAreaName";

-- OR

UPDATE "mhtc_operations"."Supply" AS s
SET "SurveyAreaID" = NULL;

UPDATE "mhtc_operations"."Supply" AS s
SET "SurveyAreaID" = a."Code"
FROM mhtc_operations."SurveyAreas" a
WHERE ST_WITHIN (s.geom, a.geom);

SELECT a."SurveyAreaName", SUM(s."RestrictionLength") AS "RestrictionLength", SUM("Capacity") AS "Total Capacity",
SUM (CASE WHEN "RestrictionTypeID" > 200 THEN 0 ELSE s."Capacity" END) AS "Bay Capacity"
FROM mhtc_operations."Supply" s, mhtc_operations."SurveyAreas2" a
WHERE a."Code" = s."SurveyAreaID"
--AND a."SurveyAreaName" LIKE 'V%'
GROUP BY a."SurveyAreaName"
ORDER BY a."SurveyAreaName";


SELECT a."CPZ", SUM(s."RestrictionLength") AS "RestrictionLength", SUM("Capacity") AS "Total Capacity",
SUM (CASE WHEN s."RestrictionTypeID" > 200 THEN 0 ELSE s."Capacity" END) AS "Bay Capacity"
FROM mhtc_operations."Supply" s, toms."ControlledParkingZones" a
WHERE ST_WITHIN (s.geom, a.geom)
--AND a."SurveyAreaName" LIKE 'V%'
GROUP BY a."CPZ"
ORDER BY a."CPZ";