#  Copyright 2021 Rikai Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from __future__ import annotations

import datetime
import os
import uuid

import mlflow
import pytest
from mlflow.tracking import MlflowClient
from pyspark.sql import SparkSession

import rikai
from rikai.contrib.tfhub.tensorflow.ssd import HUB_URL as SSD_HUB_URL
from rikai.spark.sql.codegen.mlflow_registry import CONF_MLFLOW_TRACKING_URI
from rikai.spark.utils import get_default_jar_version, init_spark_session



@pytest.fixture(scope="class")
def spark_with_mlflow(mlflow_client_http) -> SparkSession:
    mlflow_tracking_uri = mlflow.get_tracking_uri()
    print(f"Spark with mlflow tracking uri: ${mlflow_tracking_uri}")
    rikai_version = get_default_jar_version(use_snapshot=True)
    spark = init_spark_session(
        conf=dict(
            [
                (
                    "spark.jars.packages",
                    ",".join(
                        [
                            "ai.eto:rikai_2.12:{}".format(rikai_version),
                        ]
                    ),
                ),
                (
                    "spark.rikai.sql.ml.catalog.impl",
                    "ai.eto.rikai.sql.model.mlflow.MlflowCatalog",
                ),
                (
                    CONF_MLFLOW_TRACKING_URI,
                    mlflow_tracking_uri,
                ),
            ]
        ),
        app_name="rikai_with_mlflow",
    )
    yield spark

    try:
        for model in mlflow_client_http.list_registered_models():
            print(f"Cleanup {model.name}")
            mlflow_client_http.delete_registered_model(model.name)
        for run in mlflow_client_http.list_run_infos():
            print(f"Clean run: {run}")
            mlflow_client_http.delete_run(run.run_id)
    except Exception:
        pass
