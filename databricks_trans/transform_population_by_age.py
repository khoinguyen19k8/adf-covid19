# Databricks notebook source
import pyspark.sql.functions as F
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType, DecimalType

# COMMAND ----------

population_schema = StructType(
    [
        StructField("indic_de,geo\\time", StringType(), True),
        StructField("2008 ", StringType(), True),
        StructField("2009 ", StringType(), True),
        StructField("2010 ", StringType(), True),
        StructField("2011 ", StringType(), True),
        StructField("2012 ", StringType(), True),
        StructField("2013 ", StringType(), True),
        StructField("2014 ", StringType(), True),
        StructField("2015 ", StringType(), True),
        StructField("2016 ", StringType(), True),
        StructField("2017 ", StringType(), True),
        StructField("2018 ", StringType(), True),
        StructField("2019 ", StringType(), True),
    ]
)
country_lookup_schema = StructType(
    [
        StructField("country", StringType(), True),
        StructField("country_code_2_digit", StringType(), True),
        StructField("country_code_3_digit", StringType(), True),
        StructField("continent", StringType(), True),
        StructField("population", IntegerType(), True),
    ]
)

# COMMAND ----------

population_df = spark.read.option("delimiter", "\t").option("header", True).schema(population_schema).csv("dbfs:/mnt/covidreportingdlakooi/raw/population/population_by_age.tsv")
country_lookup_df = spark.read.option("header", True).schema(country_lookup_schema).csv("dbfs:/mnt/covidreportingdlakooi/lookup/dim_country/dim_country.csv")

# COMMAND ----------

population_cleaned_df = population_df.select(
    F.split(F.col("indic_de,geo\\time"), ",")[0].alias("age_group"),
    F.split(F.col("indic_de,geo\\time"), ",")[1].alias("country_code"),
    F.regexp_replace(F.col("2019 "), "[a-z]", "").cast("decimal(4,1)").alias("percentage_2019")
)

# COMMAND ----------

population_cleaned_df.filter(F.col("country_code") == "AD").select("*").show()

# COMMAND ----------

population_pivot_df = population_cleaned_df \
    .groupBy("country_code") \
    .pivot("age_group") \
    .sum("percentage_2019") \
    .orderBy("country_code")

# COMMAND ----------

population_pivot_renamed_df = population_pivot_df \
    .withColumnRenamed("PC_Y0_14", "age_group_0_14") \
    .withColumnRenamed("PC_Y15_24", "age_group_15_24") \
    .withColumnRenamed("PC_Y25_49", "age_group_25_49") \
    .withColumnRenamed("PC_Y50_64", "age_group_50_64") \
    .withColumnRenamed("PC_Y65_79", "age_group_65_79") \
    .withColumnRenamed("PC_Y80_MAX", "age_group_80_max")

# COMMAND ----------

population_final_df = population_pivot_renamed_df \
    .join(
        country_lookup_df, population_pivot_renamed_df["country_code"] == country_lookup_df["country_code_2_digit"]
    ) \
    .select(
        country_lookup_df["country"], country_lookup_df["country_code_2_digit"] ,country_lookup_df["country_code_3_digit"], country_lookup_df["population"],
        population_pivot_renamed_df["*"]
    ) \
    .drop(population_pivot_renamed_df["country_code"])

# COMMAND ----------

population_final_df.write.option("header", "true").option("delimiter", ",").mode("overwrite").csv("dbfs:/mnt/covidreportingdlakooi/processed/ecdc/population")