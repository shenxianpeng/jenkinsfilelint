#!/usr/bin/env python3
"""Pytest configuration and fixtures."""

import pytest
import tempfile
import os
from unittest.mock import patch


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean Jenkins-related environment variables for all tests."""
    jenkins_vars = ["JENKINS_URL", "JENKINS_USER", "JENKINS_TOKEN"]
    with patch.dict(
        os.environ,
        {k: v for k, v in os.environ.items() if k not in jenkins_vars},
        clear=True,
    ):
        yield


@pytest.fixture
def valid_jenkinsfile():
    """Create a temporary valid Jenkinsfile."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy") as f:
        f.write(
            """
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'echo Building'
            }
        }
        stage('Test') {
            steps {
                sh 'echo Testing'
            }
        }
    }
}
"""
        )
        f.flush()
        temp_path = f.name

    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def empty_jenkinsfile():
    """Create a temporary empty Jenkinsfile."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("")
        f.flush()
        temp_path = f.name

    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def invalid_jenkinsfile():
    """Create a temporary invalid Jenkinsfile (no pipeline declaration)."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("// Just a comment\necho 'hello world'")
        f.flush()
        temp_path = f.name

    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def library_jenkinsfile():
    """Create a temporary Jenkinsfile with @Library declaration."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(
            """
@Library('my-shared-library') _

myCustomFunction()
"""
        )
        f.flush()
        temp_path = f.name

    yield temp_path
    os.unlink(temp_path)
