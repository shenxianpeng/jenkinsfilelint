#!/usr/bin/env python3
"""Tests for the JenkinsfileLinter class."""

import os
import tempfile
from unittest.mock import patch, Mock
from jenkinsfilelint.linter import JenkinsfileLinter


class TestJenkinsfileLinterInit:
    """Test JenkinsfileLinter initialization."""

    def test_init_with_parameters(self):
        """Test initialization with explicit parameters."""
        linter = JenkinsfileLinter(
            jenkins_url="https://jenkins.example.com",
            username="testuser",
            token="testtoken",
        )
        assert linter.jenkins_url == "https://jenkins.example.com"
        assert linter.username == "testuser"
        assert linter.token == "testtoken"

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict(
            os.environ,
            {
                "JENKINS_URL": "https://jenkins.env.com",
                "JENKINS_USER": "envuser",
                "JENKINS_TOKEN": "envtoken",
            },
        ):
            linter = JenkinsfileLinter()
            assert linter.jenkins_url == "https://jenkins.env.com"
            assert linter.username == "envuser"
            assert linter.token == "envtoken"

    def test_init_parameters_override_env_vars(self):
        """Test that explicit parameters override environment variables."""
        with patch.dict(
            os.environ,
            {
                "JENKINS_URL": "https://jenkins.env.com",
                "JENKINS_USER": "envuser",
                "JENKINS_TOKEN": "envtoken",
            },
        ):
            linter = JenkinsfileLinter(
                jenkins_url="https://jenkins.param.com",
                username="paramuser",
                token="paramtoken",
            )
            assert linter.jenkins_url == "https://jenkins.param.com"
            assert linter.username == "paramuser"
            assert linter.token == "paramtoken"

    def test_init_with_no_credentials(self):
        """Test initialization without any credentials."""
        with patch.dict(os.environ, {}, clear=True):
            linter = JenkinsfileLinter()
            assert linter.jenkins_url is None
            assert linter.username is None
            assert linter.token is None


class TestJenkinsfileLinterValidateSyntax:
    """Test basic syntax validation without Jenkins."""

    def test_validate_valid_jenkinsfile(self):
        """Test validation of a valid Jenkinsfile."""
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
    }
}
"""
            )
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter()
            is_valid, message = linter._validate_syntax(temp_path)
            assert is_valid is True
            assert "appears valid" in message
        finally:
            os.unlink(temp_path)

    def test_validate_empty_file(self):
        """Test validation of an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("")
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter()
            is_valid, message = linter._validate_syntax(temp_path)
            assert is_valid is False
            assert "empty" in message.lower()
        finally:
            os.unlink(temp_path)

    def test_validate_file_without_pipeline(self):
        """Test validation of a file without pipeline declaration."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("// Just a comment\necho 'hello'")
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter()
            is_valid, message = linter._validate_syntax(temp_path)
            assert is_valid is False
            assert "pipeline declaration" in message.lower()
        finally:
            os.unlink(temp_path)

    def test_validate_file_with_library(self):
        """Test validation of a file with @Library declaration."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("@Library('my-library') _\necho 'hello'")
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter()
            is_valid, message = linter._validate_syntax(temp_path)
            assert is_valid is True
            assert "appears valid" in message
        finally:
            os.unlink(temp_path)

    def test_validate_nonexistent_file(self):
        """Test validation of a nonexistent file."""
        linter = JenkinsfileLinter()
        is_valid, message = linter._validate_syntax("/nonexistent/file.groovy")
        assert is_valid is False
        assert "Error reading file" in message


class TestJenkinsfileLinterValidateWithJenkins:
    """Test validation using Jenkins API."""

    def test_validate_without_jenkins_url(self):
        """Test validation when Jenkins URL is not set."""
        linter = JenkinsfileLinter()
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("pipeline { }")
            f.flush()
            temp_path = f.name

        try:
            is_valid, message = linter._validate_with_jenkins(temp_path)
            assert is_valid is False
            assert "Jenkins URL not provided" in message
        finally:
            os.unlink(temp_path)

    @patch("jenkinsfilelint.linter.requests.post")
    def test_validate_successful_with_text_response(self, mock_post):
        """Test successful validation with text response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Jenkinsfile successfully validated"
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("pipeline { agent any }")
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter(jenkins_url="https://jenkins.example.com")
            is_valid, message = linter._validate_with_jenkins(temp_path)
            assert is_valid is True
            assert "successfully validated" in message
        finally:
            os.unlink(temp_path)

    @patch("jenkinsfilelint.linter.requests.post")
    def test_validate_successful_with_json_response(self, mock_post):
        """Test successful validation with JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("pipeline { agent any }")
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter(jenkins_url="https://jenkins.example.com")
            is_valid, message = linter._validate_with_jenkins(temp_path)
            assert is_valid is True
            assert "successfully validated" in message
        finally:
            os.unlink(temp_path)

    @patch("jenkinsfilelint.linter.requests.post")
    def test_validate_with_errors_in_json(self, mock_post):
        """Test validation with errors in JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "error",
            "data": {"errors": ["Error 1", "Error 2"]},
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("invalid jenkinsfile")
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter(jenkins_url="https://jenkins.example.com")
            is_valid, message = linter._validate_with_jenkins(temp_path)
            assert is_valid is False
            assert "Error 1" in message
            assert "Error 2" in message
        finally:
            os.unlink(temp_path)

    @patch("jenkinsfilelint.linter.requests.post")
    def test_validate_with_json_error_no_error_list(self, mock_post):
        """Test validation with JSON error response but no errors list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "error",
            "message": "Something went wrong",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("invalid jenkinsfile")
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter(jenkins_url="https://jenkins.example.com")
            is_valid, message = linter._validate_with_jenkins(temp_path)
            assert is_valid is False
            assert "error" in message.lower()
        finally:
            os.unlink(temp_path)

    @patch("jenkinsfilelint.linter.requests.post")
    def test_validate_with_errors_in_text(self, mock_post):
        """Test validation with errors in text response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Errors encountered in validation"
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("invalid jenkinsfile")
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter(jenkins_url="https://jenkins.example.com")
            is_valid, message = linter._validate_with_jenkins(temp_path)
            assert is_valid is False
            assert "Errors" in message
        finally:
            os.unlink(temp_path)

    @patch("jenkinsfilelint.linter.requests.post")
    def test_validate_with_authentication(self, mock_post):
        """Test validation with authentication."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("pipeline { agent any }")
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter(
                jenkins_url="https://jenkins.example.com",
                username="user",
                token="token",
            )
            linter._validate_with_jenkins(temp_path)

            # Check that auth was passed to requests.post and data (not files) was used
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["auth"] == ("user", "token")
            assert "data" in call_kwargs
            assert "jenkinsfile" in call_kwargs["data"]
        finally:
            os.unlink(temp_path)

    @patch("jenkinsfilelint.linter.requests.post")
    def test_validate_connection_error(self, mock_post):
        """Test validation when connection to Jenkins fails."""
        import requests

        mock_post.side_effect = requests.exceptions.RequestException(
            "Connection refused"
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("pipeline { agent any }")
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter(jenkins_url="https://jenkins.example.com")
            is_valid, message = linter._validate_with_jenkins(temp_path)
            assert is_valid is False
            assert "Error connecting to Jenkins" in message
        finally:
            os.unlink(temp_path)

    def test_validate_with_jenkins_file_read_error(self):
        """Test validation when file cannot be read."""
        linter = JenkinsfileLinter(jenkins_url="https://jenkins.example.com")
        is_valid, message = linter._validate_with_jenkins("/nonexistent/file.groovy")
        assert is_valid is False
        assert "Error reading file" in message


class TestJenkinsfileLinterValidate:
    """Test the main validate method."""

    def test_validate_file_not_found(self):
        """Test validation when file does not exist."""
        linter = JenkinsfileLinter()
        is_valid, message = linter.validate("/nonexistent/file.groovy")
        assert is_valid is False
        assert "File not found" in message

    @patch("jenkinsfilelint.linter.requests.post")
    def test_validate_with_jenkins_url_uses_jenkins_validation(self, mock_post):
        """Test that Jenkins validation is used when URL is set."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("pipeline { agent any }")
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter(jenkins_url="https://jenkins.example.com")
            is_valid, message = linter.validate(temp_path)
            assert is_valid is True
            # Verify Jenkins API was called
            mock_post.assert_called_once()
        finally:
            os.unlink(temp_path)

    def test_validate_without_jenkins_url_uses_syntax_validation(self):
        """Test that syntax validation is used when Jenkins URL is not set."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("pipeline { agent any }")
            f.flush()
            temp_path = f.name

        try:
            linter = JenkinsfileLinter()
            is_valid, message = linter.validate(temp_path)
            assert is_valid is True
            assert "basic syntax check" in message
        finally:
            os.unlink(temp_path)
