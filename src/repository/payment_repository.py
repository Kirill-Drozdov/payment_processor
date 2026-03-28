from core.db.models import Payment
from repository.psql_repository import RepositoryPsql
from schemas.payment import PaymentRequest


class PaymentRepository(RepositoryPsql[Payment, PaymentRequest]):
    """Репозиторий для взаимодействия с объектами Платежа.
    """
    pass
