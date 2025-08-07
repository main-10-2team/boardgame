from enum import Enum


class AccountDeletionReasonEnum(str, Enum):
    DISSATISFIED = "서비스에 만족하지 않음"
    NO_FEATURES = "원하는 기능이나 콘텐츠가 없음"
    TOO_MANY_ERRORS = "사용이 불편하거나 오류가 많음"
    NO_LONGER_NEEDED = "더 이상 사용할 일이 없음"
    DUPLICATE_ACCOUNT = "계정을 중복으로 생성함"
    OTHER = "기타 (직접 입력)"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(member.name, member.value) for member in cls]
