"""Team repository type alias."""

from app.domain.aggregates.team import Team
from app.domain.value_objects import TeamId
from app.infrastructure.repositories.generic_repository import GenericRepository

# TeamRepositoryの型エイリアス
TeamRepository = GenericRepository[Team, TeamId]
