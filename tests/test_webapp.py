from io import BytesIO

import pytest

from webapp.app import create_app, resolve_jmeter_bin


@pytest.fixture()
def client(tmp_path):
    app = create_app({"TESTING": True, "WORKSPACE": tmp_path})
    return app.test_client()


def test_dashboard_is_available_without_authentication(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"JMeter Runner" in response.data


def test_jmx_upload_is_saved_and_returned_by_api(client):
    response = client.post(
        "/api/uploads",
        data={"file": (BytesIO(b"<jmeterTestPlan/>"), "smoke-test.jmx")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert response.get_json()["file"] == "smoke-test.jmx"
    assert client.get("/api/test-plans").get_json() == ["smoke-test.jmx"]


def test_upload_rejects_non_jmx_files(client):
    response = client.post(
        "/api/uploads",
        data={"file": (BytesIO(b"not a plan"), "malware.exe")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert "Only .jmx" in response.get_json()["error"]


def test_unknown_run_has_not_found_result(client):
    response = client.get("/api/runs/not-a-real-id")

    assert response.status_code == 404


def test_jmeter_home_directory_resolves_to_its_executable(tmp_path):
    jmeter_home = tmp_path / "bin"
    jmeter_home.mkdir()

    assert resolve_jmeter_bin(jmeter_home) == str(jmeter_home / "jmeter")
