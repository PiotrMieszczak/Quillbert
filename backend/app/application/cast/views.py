from app.application.dto import CharacterView
from app.domain.cast import Character


def character_view(character: Character) -> CharacterView:
    return CharacterView(
        id=character.id,
        name=character.name,
        is_player=character.is_player,
        relationship=character.relationship,
        role=character.role,
        level=character.level,
        location=character.location,
        disposition=character.disposition,
        last_seen=character.last_seen,
        stats=character.stats,
        tags=character.tags,
        quote=character.quote,
        notes=character.notes,
        bio=character.bio,
        portrait_version=None
        if character.portrait_key is None
        else character.portrait_key[:8],
        player_profile=character.player_profile,
    )
