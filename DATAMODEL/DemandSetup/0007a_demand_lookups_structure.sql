-- Demand lookups
CREATE SCHEMA IF NOT EXISTS "demand_lookups";
ALTER SCHEMA "demand_lookups" OWNER TO "postgres";

-- RestrictionTypes In Use

CREATE MATERIALIZED VIEW "demand_lookups"."SupplyRestrictionTypesInUse_View" AS
 SELECT DISTINCT "BayLineTypesInUse_View"."Code",
    "BayLineTypesInUse_View"."Description"
   FROM "toms_lookups"."BayLineTypesInUse_View",
    "mhtc_operations"."Supply"
  WHERE ("BayLineTypesInUse_View"."Code" = "Supply"."RestrictionTypeID")
  WITH DATA;

ALTER TABLE "demand_lookups"."SupplyRestrictionTypesInUse_View" OWNER TO "postgres";

-- Vehicle types

CREATE TABLE "demand_lookups"."VehicleTypes" (
    "Code" SERIAL,
    "Description" character varying
);

ALTER TABLE "demand_lookups"."VehicleTypes" OWNER TO "postgres";

ALTER TABLE demand_lookups."VehicleTypes"
    ADD PRIMARY KEY ("Code");

-- permit types

CREATE SEQUENCE "demand_lookups"."PermitTypes_Code_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE "demand_lookups"."PermitTypes_Code_seq" OWNER TO "postgres";

CREATE TABLE "demand_lookups"."PermitTypes" (
    "Code" SERIAL,
    "Description" character varying
);

ALTER TABLE "demand_lookups"."PermitTypes" OWNER TO "postgres";

ALTER TABLE demand_lookups."PermitTypes"
    ADD PRIMARY KEY ("Code");
