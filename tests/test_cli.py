#!/usr/bin/env python3
"""Tests for the CLI module."""

import os
import pytest
import tempfile
from unittest.mock import patch, Mock
from jenkinsfilelint.cli import main


class TestCLIMain:
    """Test the CLI main function."""

    def test_help_message(self):
        """Test that help message is displayed."""
        with patch("sys.argv", ["jenkinsfilelint", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_validate_single_valid_file(self):
        """Test validation of a single valid file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy") as f:
            f.write("pipeline { agent any }")
            f.flush()
            temp_path = f.name

        try:
            with patch("sys.argv", ["jenkinsfilelint", temp_path]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
        finally:
            os.unlink(temp_path)

    def test_validate_single_invalid_file(self, capsys):
        """Test validation of a single invalid file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("")  # Empty file
            f.flush()
            temp_path = f.name

        try:
            with patch("sys.argv", ["jenkinsfilelint", temp_path]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "Invalid" in captured.err
            assert "empty" in captured.err.lower()
        finally:
            os.unlink(temp_path)

    def test_validate_multiple_files(self):
        """Test validation of multiple files."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix="1.groovy"
        ) as f1:
            f1.write("pipeline { agent any }")
            f1.flush()
            temp_path1 = f1.name

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix="2.groovy"
        ) as f2:
            f2.write("@Library('lib') _\necho 'test'")
            f2.flush()
            temp_path2 = f2.name

        try:
            with patch("sys.argv", ["jenkinsfilelint", temp_path1, temp_path2]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)

    def test_validate_multiple_files_with_one_invalid(self, capsys):
        """Test validation of multiple files where one is invalid."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix="1.groovy"
        ) as f1:
            f1.write("pipeline { agent any }")
            f1.flush()
            temp_path1 = f1.name

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix="2.groovy"
        ) as f2:
            f2.write("")  # Empty file
            f2.flush()
            temp_path2 = f2.name

        try:
            with patch("sys.argv", ["jenkinsfilelint", temp_path1, temp_path2]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)

    def test_validate_with_verbose_flag(self, capsys):
        """Test validation with verbose output."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy") as f:
            f.write("pipeline { agent any }")
            f.flush()
            temp_path = f.name

        try:
            with patch("sys.argv", ["jenkinsfilelint", "--verbose", temp_path]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0

            captured = capsys.readouterr()
            assert "Validating" in captured.out
            assert "appears valid" in captured.out
        finally:
            os.unlink(temp_path)

    def test_validate_with_jenkins_url_argument(self):
        """Test validation with Jenkins URL argument."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy") as f:
            f.write("pipeline { agent any }")
            f.flush()
            temp_path = f.name

        try:
            with patch(
                "sys.argv",
                [
                    "jenkinsfilelint",
                    "--jenkins-url",
                    "https://jenkins.example.com",
                    temp_path,
                ],
            ):
                with patch("jenkinsfilelint.linter.requests.post") as mock_post:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"status": "ok"}
                    mock_response.raise_for_status = Mock()
                    mock_post.return_value = mock_response

                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    assert exc_info.value.code == 0
                    mock_post.assert_called_once()
        finally:
            os.unlink(temp_path)

    def test_validate_with_username_and_token_arguments(self):
        """Test validation with username and token arguments."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy") as f:
            f.write("pipeline { agent any }")
            f.flush()
            temp_path = f.name

        try:
            with patch(
                "sys.argv",
                [
                    "jenkinsfilelint",
                    "--jenkins-url",
                    "https://jenkins.example.com",
                    "--username",
                    "testuser",
                    "--token",
                    "testtoken",
                    temp_path,
                ],
            ):
                with patch("jenkinsfilelint.linter.requests.post") as mock_post:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"status": "ok"}
                    mock_response.raise_for_status = Mock()
                    mock_post.return_value = mock_response

                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    assert exc_info.value.code == 0

                    # Verify authentication was used
                    call_kwargs = mock_post.call_args[1]
                    assert call_kwargs["auth"] == ("testuser", "testtoken")
        finally:
            os.unlink(temp_path)

    def test_validate_nonexistent_file(self, capsys):
        """Test validation of a nonexistent file."""
        with patch("sys.argv", ["jenkinsfilelint", "/nonexistent/file.groovy"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "File not found" in captured.err

    def test_validate_with_env_variables(self):
        """Test validation using environment variables for configuration."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy") as f:
            f.write("pipeline { agent any }")
            f.flush()
            temp_path = f.name

        try:
            with patch.dict(
                os.environ,
                {
                    "JENKINS_URL": "https://jenkins.env.com",
                    "JENKINS_USER": "envuser",
                    "JENKINS_TOKEN": "envtoken",
                },
            ):
                with patch("sys.argv", ["jenkinsfilelint", temp_path]):
                    with patch("jenkinsfilelint.linter.requests.post") as mock_post:
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {"status": "ok"}
                        mock_response.raise_for_status = Mock()
                        mock_post.return_value = mock_response

                        with pytest.raises(SystemExit) as exc_info:
                            main()
                        assert exc_info.value.code == 0

                        # Verify Jenkins API was called
                        mock_post.assert_called_once()
                        call_kwargs = mock_post.call_args[1]
                        assert call_kwargs["auth"] == ("envuser", "envtoken")
        finally:
            os.unlink(temp_path)
