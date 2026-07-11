from app.services.lineup_service import LineupService


def test_lineup_projection_selects_formation_shape():
    squad = []
    for position, count in (("Goalkeeper", 2), ("Defence", 6), ("Midfield", 5), ("Offence", 5)):
        squad.extend({"id": len(squad) + 1, "name": f"Player {len(squad) + 1}", "position": position} for _ in range(count))
    projection = LineupService.project({"name": "Test FC", "squad": squad, "coach": {"name": "Coach"}})
    assert projection["formation"] == "4-3-3"
    assert len(projection["players"]) == 11
    assert projection["status"] == "squad-based projection"
