from app.models.dashboard import Dashboard
from app.models.metric import Metric
from app.models.user import User


def test_user_model():
    # ✅ Правильное название: password_hash
    user = User(id=1, email="test@example.com", password_hash="hashed", role="user")
    assert user.email == "test@example.com"
    assert user.role == "user"


def test_metric_model():
    metric = Metric(
        id=1, name="test_metric", metric_type="counter", value=100.0, dashboard_id=1
    )
    assert metric.name == "test_metric"
    assert metric.metric_type == "counter"
    assert metric.value == 100.0


def test_dashboard_model():
    dashboard = Dashboard(id=1, name="test_dashboard", owner_id=1)
    assert dashboard.name == "test_dashboard"
    assert dashboard.owner_id == 1
