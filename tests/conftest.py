#!/usr/bin/env python3
"""Pytest configuration and fixtures."""

import pytest
import tempfile
import os


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean Jenkins-related environment variables for all tests."""
    jenkins_vars = ["JENKINS_URL", "JENKINS_USER", "JENKINS_TOKEN"]
    # Save the original values
    original_values = {k: os.environ.get(k) for k in jenkins_vars}

    # Remove Jenkins variables
    for var in jenkins_vars:
        os.environ.pop(var, None)

    yield

    # Restore original values
    for k, v in original_values.items():
        if v is not None:
            os.environ[k] = v
        else:
            os.environ.pop(k, None)


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
