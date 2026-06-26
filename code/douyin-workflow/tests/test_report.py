from app.report.daily_report import build_report


def test_build_report_counts_completed_videos() -> None:
    records = [
        {
            "video_id": "1",
            "video": {
                "creator_name": "博主 A",
                "title": "标题 A",
                "publish_time": "2026-06-26T09:15:00+08:00",
                "like_count": 100,
                "comment_count": 20,
                "share_count": 3,
            },
            "analysis_status": "completed",
            "analysis": {
                "summary": "总结 A",
                "keywords": ["AI 工作流", "效率工具"],
                "key_points": ["点 1"],
                "clean_copy": "文案 A",
            },
        },
        {
            "video_id": "2",
            "video": {
                "creator_name": "博主 B",
                "title": "标题 B",
                "publish_time": "2026-06-26T11:15:00+08:00",
                "like_count": 50,
                "comment_count": 10,
                "share_count": 1,
            },
            "analysis_status": "pending",
            "analysis": {},
        },
    ]

    report = build_report(records, "2026-06-26", 5)

    assert report["video_count"] == 1
    assert report["creator_breakdown"] == {"博主 A": 1}
    assert report["top_keywords"][0]["keyword"] == "AI 工作流"
