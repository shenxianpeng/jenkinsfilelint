#!/usr/bin/env python3
"""Tests for the CLI module."""

import os
import pytest
import tempfile
from unittest.mock import patch, Mock
from jenkinsfilelint.cli import main, should_skip_file, should_include_file


class TestCLIMain:
    """Test the CLI main function."""

    def test_help_message(self):
        """Test that help message is displayed."""
        with patch("sys.argv", ["jenkinsfilelint", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_validate_single_valid_file(self, capsys):
        """Test validation of a single valid file requires credentials."""
        f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy")
        f.write("pipeline { agent any }")
        f.flush()
        f.close()
        temp_path = f.name

        try:
            with patch("sys.argv", ["jenkinsfilelint", temp_path]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "credentials required" in captured.err.lower()
        finally:
            os.unlink(temp_path)

    def test_validate_single_invalid_file(self, capsys):
        """Test validation of a single invalid file."""
        f = tempfile.NamedTemporaryFile(mode="w", delete=False)
        f.write("")  # Empty file
        f.flush()
        f.close()
        temp_path = f.name

        try:
            with patch("sys.argv", ["jenkinsfilelint", temp_path]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

            captured = capsys.readouterr()
            # Error message is printed without filename prefix for deduplication
            assert "credentials required" in captured.err.lower()
        finally:
            os.unlink(temp_path)

    def test_validate_multiple_files(self, capsys):
        """Test validation of multiple files requires credentials.

        Error messages should be deduplicated - the same error should only
        appear once even when multiple files have the same error.
        """
        f1 = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="1.groovy")
        f1.write("pipeline { agent any }")
        f1.flush()
        f1.close()
        temp_path1 = f1.name

        f2 = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="2.groovy")
        f2.write("@Library('lib') _\necho 'test'")
        f2.flush()
        f2.close()
        temp_path2 = f2.name

        try:
            with patch("sys.argv", ["jenkinsfilelint", temp_path1, temp_path2]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

            captured = capsys.readouterr()
            # Verify the error is present
            assert "credentials required" in captured.err.lower()
            # Verify deduplication - the credentials message should appear exactly once
            assert captured.err.lower().count("credentials required") == 1
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)

    def test_validate_multiple_files_with_one_invalid(self, capsys):
        """Test validation of multiple files where one is invalid."""
        f1 = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="1.groovy")
        f1.write("pipeline { agent any }")
        f1.flush()
        f1.close()
        temp_path1 = f1.name

        f2 = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="2.groovy")
        f2.write("")  # Empty file
        f2.flush()
        f2.close()
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
        """Test validation with verbose output requires credentials."""
        f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy")
        f.write("pipeline { agent any }")
        f.flush()
        f.close()
        temp_path = f.name

        try:
            with patch("sys.argv", ["jenkinsfilelint", "--verbose", temp_path]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "Validating" in captured.out
            assert "credentials required" in captured.err.lower()
        finally:
            os.unlink(temp_path)

    def test_validate_with_jenkins_url_argument(self):
        """Test validation with Jenkins URL argument."""
        f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy")
        f.write("pipeline { agent any }")
        f.flush()
        f.close()
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
        f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy")
        f.write("pipeline { agent any }")
        f.flush()
        f.close()
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
        f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy")
        f.write("pipeline { agent any }")
        f.flush()
        f.close()
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


class TestShouldSkipFile:
    """Test the should_skip_file function."""

    def test_no_skip_patterns(self):
        """Test that no file is skipped when no patterns are provided."""
        assert should_skip_file("src/MyClass.groovy", []) is False
        assert should_skip_file("Jenkinsfile", []) is False
        assert should_skip_file("Jenkinsfile", None) is False

    def test_exact_match(self):
        """Test exact filename match."""
        assert should_skip_file("src/Utils.groovy", ["src/Utils.groovy"]) is True
        assert should_skip_file("src/Other.groovy", ["src/Utils.groovy"]) is False

    def test_glob_pattern_wildcard(self):
        """Test glob pattern with wildcard."""
        assert should_skip_file("src/Utils.groovy", ["*.groovy"]) is True
        assert should_skip_file("src/Utils.groovy", ["src/*.groovy"]) is True
        assert should_skip_file("Jenkinsfile", ["*.groovy"]) is False

    def test_glob_pattern_double_wildcard(self):
        """Test glob pattern with directory wildcard."""
        patterns = ["*/src/*.groovy"]
        assert should_skip_file("lib/src/MyClass.groovy", patterns) is True
        assert should_skip_file("vars/deploy.groovy", patterns) is False

    def test_multiple_patterns(self):
        """Test multiple skip patterns."""
        patterns = ["*/src/*.groovy", "vars/*.groovy"]
        assert should_skip_file("lib/src/MyClass.groovy", patterns) is True
        assert should_skip_file("vars/deploy.groovy", patterns) is True
        assert should_skip_file("Jenkinsfile", patterns) is False


class TestCLISkipOption:
    """Test the CLI --skip option."""

    def test_skip_single_file(self, capsys):
        """Test skipping a single file with --skip option."""
        f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy")
        f.write("class Utils { }")  # Pure Groovy, not a pipeline
        f.flush()
        f.close()
        temp_path = f.name

        try:
            with patch(
                "sys.argv",
                ["jenkinsfilelint", "--skip", "*.groovy", temp_path],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                # Should exit 0 because the only file was skipped
                assert exc_info.value.code == 0
        finally:
            os.unlink(temp_path)

    def test_skip_single_file_verbose(self, capsys):
        """Test skipping a file with verbose output."""
        f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".groovy")
        f.write("class Utils { }")
        f.flush()
        f.close()
        temp_path = f.name

        try:
            with patch(
                "sys.argv",
                ["jenkinsfilelint", "--verbose", "--skip", "*.groovy", temp_path],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0

            captured = capsys.readouterr()
            assert "Skipped" in captured.out
            assert "matches skip pattern" in captured.out
        finally:
            os.unlink(temp_path)

    def test_skip_some_files_validate_others(self, capsys):
        """Test skipping some files while validating others."""
        # Create a groovy file to skip
        groovy_dir = tempfile.mkdtemp()
        groovy_file = os.path.join(groovy_dir, "Utils.groovy")
        with open(groovy_file, "w") as f:
            f.write("class Utils { }")

        # Create a Jenkinsfile to validate
        jenkinsfile = tempfile.NamedTemporaryFile(
            mode="w", delete=False, prefix="Jenkinsfile"
        )
        jenkinsfile.write("pipeline { agent any }")
        jenkinsfile.flush()
        jenkinsfile.close()
        jenkinsfile_path = jenkinsfile.name

        try:
            with patch(
                "sys.argv",
                [
                    "jenkinsfilelint",
                    "--jenkins-url",
                    "https://jenkins.example.com",
                    "--skip",
                    "*.groovy",
                    groovy_file,
                    jenkinsfile_path,
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
                    # Only Jenkinsfile should be validated, groovy file skipped
                    mock_post.assert_called_once()
        finally:
            os.unlink(groovy_file)
            os.rmdir(groovy_dir)
            os.unlink(jenkinsfile_path)

    def test_multiple_skip_patterns(self, capsys):
        """Test using multiple --skip options."""
        # Create files in temp directories
        src_dir = tempfile.mkdtemp()
        vars_dir = tempfile.mkdtemp()

        src_file = os.path.join(src_dir, "Utils.groovy")
        with open(src_file, "w") as f:
            f.write("class Utils { }")

        vars_file = os.path.join(vars_dir, "deploy.groovy")
        with open(vars_file, "w") as f:
            f.write("def call() { }")

        try:
            with patch(
                "sys.argv",
                [
                    "jenkinsfilelint",
                    "--skip",
                    "*/Utils.groovy",
                    "--skip",
                    "*/deploy.groovy",
                    src_file,
                    vars_file,
                ],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                # Both files skipped, so exit 0
                assert exc_info.value.code == 0
        finally:
            os.unlink(src_file)
            os.unlink(vars_file)
            os.rmdir(src_dir)
            os.rmdir(vars_dir)


class TestShouldIncludeFile:
    """Test the should_include_file function."""

    def test_no_include_patterns(self):
        """Test that all files are included when no patterns are provided."""
        assert should_include_file("src/MyClass.groovy", []) is True
        assert should_include_file("Jenkinsfile", []) is True
        assert should_include_file("Jenkinsfile", None) is True

    def test_exact_match(self):
        """Test exact filename match."""
        assert should_include_file("Jenkinsfile", ["Jenkinsfile"]) is True
        assert should_include_file("src/Other.groovy", ["Jenkinsfile"]) is False

    def test_glob_pattern_wildcard(self):
        """Test glob pattern with wildcard."""
        assert should_include_file("Jenkinsfile.prod", ["Jenkinsfile*"]) is True
        assert should_include_file("Jenkinsfile", ["Jenkinsfile*"]) is True
        assert should_include_file("src/Utils.groovy", ["Jenkinsfile*"]) is False

    def test_glob_pattern_double_wildcard(self):
        """Test glob pattern with directory wildcard."""
        patterns = ["*/pipelines/*.groovy"]
        assert should_include_file("project/pipelines/build.groovy", patterns) is True
        assert should_include_file("src/utils.groovy", patterns) is False

    def test_multiple_patterns(self):
        """Test multiple include patterns."""
        patterns = ["Jenkinsfile*", "*/pipelines/*.groovy"]
        assert should_include_file("Jenkinsfile", patterns) is True
        assert should_include_file("Jenkinsfile.prod", patterns) is True
        assert should_include_file("project/pipelines/build.groovy", patterns) is True
        assert should_include_file("src/Utils.groovy", patterns) is False


class TestCLIIncludeOption:
    """Test the CLI --include option."""

    def test_include_single_file(self, capsys):
        """Test including a single file with --include option."""
        # Create a Jenkinsfile that should be included
        jenkinsfile = tempfile.NamedTemporaryFile(
            mode="w", delete=False, prefix="Jenkinsfile"
        )
        jenkinsfile.write("pipeline { agent any }")
        jenkinsfile.flush()
        jenkinsfile.close()
        jenkinsfile_path = jenkinsfile.name

        # Create a groovy file that should not be included
        groovy_dir = tempfile.mkdtemp()
        groovy_file = os.path.join(groovy_dir, "Utils.groovy")
        with open(groovy_file, "w") as f:
            f.write("class Utils { }")

        try:
            with patch(
                "sys.argv",
                [
                    "jenkinsfilelint",
                    "--jenkins-url",
                    "https://jenkins.example.com",
                    "--include",
                    "Jenkinsfile*",
                    jenkinsfile_path,
                    groovy_file,
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
                    # Only Jenkinsfile should be validated, groovy file not included
                    mock_post.assert_called_once()
        finally:
            os.unlink(jenkinsfile_path)
            os.unlink(groovy_file)
            os.rmdir(groovy_dir)

    def test_include_single_file_verbose(self, capsys):
        """Test including a file with verbose output."""
        # Create a Jenkinsfile that should be included
        jenkinsfile = tempfile.NamedTemporaryFile(
            mode="w", delete=False, prefix="Jenkinsfile"
        )
        jenkinsfile.write("pipeline { agent any }")
        jenkinsfile.flush()
        jenkinsfile.close()
        jenkinsfile_path = jenkinsfile.name

        # Create a groovy file that should not be included
        groovy_dir = tempfile.mkdtemp()
        groovy_file = os.path.join(groovy_dir, "Utils.groovy")
        with open(groovy_file, "w") as f:
            f.write("class Utils { }")

        try:
            with patch(
                "sys.argv",
                [
                    "jenkinsfilelint",
                    "--verbose",
                    "--jenkins-url",
                    "https://jenkins.example.com",
                    "--include",
                    "Jenkinsfile*",
                    jenkinsfile_path,
                    groovy_file,
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

            captured = capsys.readouterr()
            # Groovy file should be skipped with include pattern message
            assert "Skipped" in captured.out
            assert "does not match include pattern" in captured.out
        finally:
            os.unlink(jenkinsfile_path)
            os.unlink(groovy_file)
            os.rmdir(groovy_dir)

    def test_include_all_files_skipped(self, capsys):
        """Test that exit code is 0 when all files are skipped due to include pattern."""
        groovy_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".groovy"
        )
        groovy_file.write("class Utils { }")
        groovy_file.flush()
        groovy_file.close()
        groovy_path = groovy_file.name

        try:
            with patch(
                "sys.argv",
                [
                    "jenkinsfilelint",
                    "--include",
                    "Jenkinsfile*",
                    groovy_path,
                ],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                # Should exit 0 because the only file was skipped
                assert exc_info.value.code == 0
        finally:
            os.unlink(groovy_path)

    def test_multiple_include_patterns(self, capsys):
        """Test using multiple --include options."""
        # Create files to test
        jenkinsfile1 = tempfile.NamedTemporaryFile(
            mode="w", delete=False, prefix="Jenkinsfile"
        )
        jenkinsfile1.write("pipeline { agent any }")
        jenkinsfile1.flush()
        jenkinsfile1.close()
        jenkinsfile1_path = jenkinsfile1.name

        # Create a pipeline groovy file
        pipelines_dir = tempfile.mkdtemp()
        pipeline_file = os.path.join(pipelines_dir, "build.groovy")
        with open(pipeline_file, "w") as f:
            f.write("pipeline { agent any }")

        # Create a utils groovy file (should not be included)
        utils_dir = tempfile.mkdtemp()
        utils_file = os.path.join(utils_dir, "Utils.groovy")
        with open(utils_file, "w") as f:
            f.write("class Utils { }")

        try:
            with patch(
                "sys.argv",
                [
                    "jenkinsfilelint",
                    "--jenkins-url",
                    "https://jenkins.example.com",
                    "--include",
                    "Jenkinsfile*",
                    "--include",
                    "*/build.groovy",
                    jenkinsfile1_path,
                    pipeline_file,
                    utils_file,
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
                    # Both Jenkinsfile and build.groovy should be validated
                    assert mock_post.call_count == 2
        finally:
            os.unlink(jenkinsfile1_path)
            os.unlink(pipeline_file)
            os.unlink(utils_file)
            os.rmdir(pipelines_dir)
            os.rmdir(utils_dir)

    def test_include_and_skip_combined(self, capsys):
        """Test using both --include and --skip options together."""
        # Create files to test
        jenkinsfile1 = tempfile.NamedTemporaryFile(
            mode="w", delete=False, prefix="Jenkinsfile"
        )
        jenkinsfile1.write("pipeline { agent any }")
        jenkinsfile1.flush()
        jenkinsfile1.close()
        jenkinsfile1_path = jenkinsfile1.name

        # Create Jenkinsfile.prod (should be excluded by skip)
        jenkinsfile2 = tempfile.NamedTemporaryFile(
            mode="w", delete=False, prefix="Jenkinsfile", suffix=".prod"
        )
        jenkinsfile2.write("pipeline { agent any }")
        jenkinsfile2.flush()
        jenkinsfile2.close()
        jenkinsfile2_path = jenkinsfile2.name

        try:
            with patch(
                "sys.argv",
                [
                    "jenkinsfilelint",
                    "--jenkins-url",
                    "https://jenkins.example.com",
                    "--include",
                    "Jenkinsfile*",
                    "--skip",
                    "*.prod",
                    jenkinsfile1_path,
                    jenkinsfile2_path,
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
                    # Only first Jenkinsfile validated (second skipped)
                    mock_post.assert_called_once()
        finally:
            os.unlink(jenkinsfile1_path)
            os.unlink(jenkinsfile2_path)
