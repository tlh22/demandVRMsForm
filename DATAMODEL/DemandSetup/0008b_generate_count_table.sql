
DROP TABLE IF EXISTS demand."Counts" CASCADE;

CREATE TABLE "demand"."Counts" (
  "SurveyID" integer NOT NULL,
  "GeometryID" character varying(12) NOT NULL,

  "NrCars" integer,
  "NrLGVs" integer,
  "NrMCLs" integer,
  "NrTaxis" integer,
  "NrPCLs" integer,
  "NrEScooters" integer,
  "NrDocklessPCLs" integer,
  "NrOGVs" integer,
  "NrMiniBuses" integer,
  "NrBuses" integer,
  "NrSpaces" integer,
  "Notes" character varying(10000) COLLATE pg_catalog."default",

  "DoubleParkingDetails" character varying COLLATE pg_catalog."default",

  "NrCars_Suspended" integer,
  "NrLGVs_Suspended" integer,
  "NrMCLs_Suspended" integer,
  "NrTaxis_Suspended" integer,
  "NrPCLs_Suspended" integer,
  "NrEScooters_Suspended" integer,
  "NrDocklessPCLs_Suspended" integer,
  "NrOGVs_Suspended" integer,
  "NrMiniBuses_Suspended" integer,
  "NrBuses_Suspended" integer,

   CONSTRAINT "Counts_pkey" PRIMARY KEY ("SurveyID", "GeometryID")
)
WITH (
  OIDS=FALSE
);

ALTER TABLE demand."Counts"
  OWNER TO postgres;

CREATE UNIQUE INDEX "Counts_unique_idx"
ON demand."Counts"("SurveyID", "GeometryID");

-- and populate

INSERT INTO "demand"."Counts" ("SurveyID", "GeometryID")
SELECT "SurveyID", "GeometryID"
FROM mhtc_operations."Supply" r, demand."Surveys";


/***
UPDATE "demand"."Counts"
SET

ALTER TABLE "demand"."Counts" DROP CONSTRAINT "Counts_pkey";
ALTER TABLE "demand"."Counts" ADD PRIMARY KEY ("SurveyID", "GeometryID");
ALTER TABLE IF EXISTS demand."Counts" DROP COLUMN IF EXISTS "ID";
ALTER TABLE IF EXISTS demand."Counts" DROP COLUMN IF EXISTS "SectionID";

***/