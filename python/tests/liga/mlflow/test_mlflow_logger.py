#  Copyright (c) 2021 Rikai Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import mlflow
from mlflow.entities.model_registry import ModelVersion
from mlflow.tracking import MlflowClient

import rikai
import sklearn
from liga.sklearn.mlflow import log_model


def test_none_value_tags(mlflow_tracking_uri: str, sklearn_lr_uri: str):
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    with mlflow.start_run():
        model = mlflow.sklearn.load_model(sklearn_lr_uri)
        log_model(
            model,
            "artifact_path",
            "output_schema",
        )
        run_id = mlflow.active_run().info.run_id
        run = mlflow.get_run(run_id)
        tags = run.data.tags
        assert tags[rikai.mlflow.CONF_MLFLOW_ARTIFACT_PATH] == "artifact_path"
        assert tags[rikai.mlflow.CONF_MLFLOW_OUTPUT_SCHEMA] == "output_schema"


# def test_model_and_version_tags(mlflow_tracking_uri: str, resnet_model_uri):
#     mlflow.set_tracking_uri(mlflow_tracking_uri)
#     model_name = "model_for_tags"
#     c = MlflowClient()
#     c.create_registered_model(model_name)
#
#     def run_one_time(expected_tags):
#         with mlflow.start_run():
#             model = torch.load(resnet_model_uri)
#             rikai.mlflow.pytorch.log_model(
#                 model,
#                 registered_model_name=model_name,
#                 **expected_tags,
#             )
#             run_id = mlflow.active_run().info.run_id
#             run = mlflow.get_run(run_id)
#             tags = run.data.tags
#
#         logged_model = c.get_registered_model(model_name)
#         print(f"current logged model {logged_model}")
#         assert (
#                 logged_model.tags[rikai.mlflow.CONF_MLFLOW_ARTIFACT_PATH]
#                 == tags[rikai.mlflow.CONF_MLFLOW_ARTIFACT_PATH]
#         )
#         assert (
#                 expected_tags["artifact_path"]
#                 == tags[rikai.mlflow.CONF_MLFLOW_ARTIFACT_PATH]
#         )
#         assert (
#                 logged_model.tags[rikai.mlflow.CONF_MLFLOW_OUTPUT_SCHEMA]
#                 == tags[rikai.mlflow.CONF_MLFLOW_OUTPUT_SCHEMA]
#         )
#         assert (
#                 logged_model.tags[rikai.mlflow.CONF_MLFLOW_MODEL_FLAVOR]
#                 == "pytorch"
#         )
#         all_versions = c.get_latest_versions(
#             model_name, stages=["production", "staging", "None"]
#         )
#         current_version: ModelVersion = None
#         for v in all_versions:
#             if v.run_id == run_id:
#                 current_version = v
#                 break
#         if current_version is None:
#             raise ValueError(
#                 "No model version found matching runid: {}".format(run_id)
#             )
#         print(f"current version {current_version}")
#         assert (
#                 current_version.tags[rikai.mlflow.CONF_MLFLOW_ARTIFACT_PATH]
#                 == tags[rikai.mlflow.CONF_MLFLOW_ARTIFACT_PATH]
#         )
#         assert (
#                 current_version.tags[rikai.mlflow.CONF_MLFLOW_OUTPUT_SCHEMA]
#                 == tags[rikai.mlflow.CONF_MLFLOW_OUTPUT_SCHEMA]
#         )
#         assert (
#                 current_version.tags[rikai.mlflow.CONF_MLFLOW_MODEL_FLAVOR]
#                 == "pytorch"
#         )
#
#     expected_tags = {"artifact_path": "fake_path1", "schema": "fake_schema1"}
#     run_one_time(expected_tags)
#
#     # verify the tags would be overwritten by new runs
#     expected_tags2 = {"artifact_path": "fake_path2", "schema": "fake_schema2"}
#     run_one_time(expected_tags2)