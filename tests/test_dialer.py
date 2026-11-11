from rva.dialer import CampaignDialer


def test_enqueue_lab_job() -> None:
    dialer = CampaignDialer(name="lab")
    job = dialer.enqueue("sip:1001@127.0.0.1")
    snap = dialer.snapshot()
    assert snap["campaign"] == "lab"
    assert snap["jobs"][0]["job_id"] == job.job_id
    assert snap["jobs"][0]["status"] == "queued"
