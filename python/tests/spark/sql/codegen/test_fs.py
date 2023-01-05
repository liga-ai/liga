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

import secrets
import uuid
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest
import torch
import yaml
from pandas.core.series import Series
from py4j.protocol import Py4JJavaError
from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType, StructField, StructType
from torch.utils.data import DataLoader
from utils import check_ml_predict

from rikai.pytorch.pandas import PandasDataset
from rikai.spark.sql.codegen.fs import FileModelSpec
from rikai.spark.sql.exceptions import SpecError
from rikai.testing.utils import apply_model_spec


def spec_file(content: Dict[str, Any], tmp_path: Path) -> str:
    filename = f"{secrets.token_urlsafe(6)}.yml"
    spec_filepath = tmp_path / filename
    with spec_filepath.open(mode="w") as fobj:
        yaml.dump(content, fobj)
    return str(spec_filepath)


def test_validate_yaml_spec(tmp_path):
    spec = FileModelSpec(
        {
            "uri": spec_file(
                {
                    "version": "1.2",
                    "name": "test_yaml_model",
                    "schema": "long",
                    "model": {
                        "uri": "s3://bucket/to/model.pt",
                        "flavor": "pytorch",
                        "type": "resnet",
                        "unspecified_field": True,
                    },
                    "options": {"gpu": "true", "batch_size": 123},
                },
                tmp_path,
            )
        }
    )

    assert spec.name == "test_yaml_model"
    assert spec.model_uri == "s3://bucket/to/model.pt"


def test_validate_misformed_spec(tmp_path):
    with pytest.raises(SpecError):
        FileModelSpec({})

    with pytest.raises(SpecError, match=".*version' is a required property.*"):
        FileModelSpec(
            {
                "uri": spec_file(
                    {
                        "name": "test_yaml_model",
                        "schema": "long",
                        "model": {
                            "uri": "s3://foo/bar",
                            "flavor": "pytorch",
                            "type": "resnet",
                        },
                    },
                    tmp_path,
                )
            }
        )

    with pytest.raises(
        SpecError, match=".*Missing model flavor or model type"
    ):
        FileModelSpec(
            {
                "uri": spec_file(
                    {
                        "version": "1.0",
                        "name": "test_yaml_model",
                        "schema": "long",
                    },
                    tmp_path,
                )
            }
        )

    with pytest.raises(
        SpecError, match=".*Missing model flavor or model type"
    ):
        FileModelSpec(
            {
                "uri": spec_file(
                    {
                        "version": "1.0",
                        "name": "test_yaml_model",
                        "schema": "long",
                        "model": {},
                    },
                    tmp_path,
                )
            }
        )


def test_construct_spec_with_options(tmp_path):
    spec = FileModelSpec(
        {
            "uri": spec_file(
                {
                    "version": "1.0",
                    "name": "with_options",
                    "schema": "int",
                    "model": {
                        "uri": "s3://bucket/to/model.pt",
                        "flavor": "pytorch",
                        "type": "ssd",
                        "unspecified_field": True,
                    },
                    "options": {"foo": 1, "bar": "2.3"},
                },
                tmp_path,
            )
        }
    )
    assert {"foo": 1, "bar": "2.3"} == spec.options
    assert "s3://bucket/to/model.pt" == spec.model_uri


@pytest.mark.timeout(120)
def test_yaml_model(
    spark: SparkSession, resnet_spec: str, two_flickr_rows: list
):
    spark.sql("CREATE MODEL resnet_m USING 'file://{}'".format(resnet_spec))
    check_ml_predict(spark, "resnet_m", two_flickr_rows)


def test_yaml_model_type(resnet_spec: str, two_flickr_images):
    spec = FileModelSpec({"uri": resnet_spec})
    inputs = [pd.Series(image) for image in two_flickr_images]
    results = apply_model_spec(spec, inputs)
    assert len(results) == 2
    for series in results:
        assert len(series[0]) > 10


def test_load_pth_file_without_model_type(
    spark: SparkSession, resnet_model_uri: str
):
    with pytest.raises(Py4JJavaError):
        spark.sql(
            """CREATE OR REPLACE MODEL fasterrcnn
            USING 'file://{}'
            """.format(
                resnet_model_uri
            )
        )


def test_relative_model_uri(tmp_path):
    spec = FileModelSpec(
        {
            "uri": spec_file(
                {
                    "version": "1.2",
                    "name": "test_yaml_model",
                    "schema": "long",
                    "model": {
                        "uri": "model.pt",
                        "type": "ssd",
                        "flavor": "pytorch",
                    },
                },
                tmp_path,
            )
        }
    )
    assert Path(spec.model_uri) == tmp_path / "model.pt"


def test_spec_with_labels(tmp_path):
    import json

    from rikai.pytorch.models.torch import COCO_INSTANCE_CATEGORY_NAMES

    with open(tmp_path / "labels.json", "w") as fh:
        json.dump(COCO_INSTANCE_CATEGORY_NAMES, fh)

    spec = FileModelSpec(
        {
            "uri": spec_file(
                {
                    "version": "1.2",
                    "name": "test_yaml_model",
                    "schema": "long",
                    "model": {
                        "uri": "s3://bucket/to/model.pt",
                        "flavor": "pytorch",
                        "type": "resnet50",
                        "unspecified_field": True,
                    },
                    "labels": {"uri": str(tmp_path / "labels.json")},
                    "options": {"gpu": "true", "batch_size": 123},
                },
                tmp_path,
            )
        }
    )

    assert spec.name == "test_yaml_model"
    assert spec.model_uri == "s3://bucket/to/model.pt"
    assert spec.load_label_fn()(1) == "person"
