import logging
from typing import Any, cast

from django.db import IntegrityError
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.games.models import Game
from apps.games.serializers.admin_boardgame_serializers import (
    AdminGameRegisterSerializer,
    AdminGameUpdateSerializer,
)
from core.utils.permission import IsAdminRole
from core.utils.s3_file_upload import S3Uploader

logger = logging.getLogger(__name__)


# 관리자 보드 게임 등록 API
@extend_schema(
    tags=["[Admin]"],
    summary="관리자 보드 게임 등록",
    description="새로운 보드 게임 정보를 시스템에 추가합니다. title은 고유해야 합니다.",
    request=AdminGameRegisterSerializer,
)
# 관리자용 보드 게임 등록 API 엔드포인트입니다.
class AdminGameRegisterView(generics.CreateAPIView[Game]):

    queryset = Game.objects.all()
    serializer_class = AdminGameRegisterSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    # POST 요청을 처리하고 커스텀 응답 형식을 반환하기 위해 create 메서드를 오버라이드
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AdminGameRegisterSerializer(data=request.data)
        try:

            serializer.is_valid(raise_exception=True)
            game_instance = serializer.save()

            # 성공적인 응답
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            # 시리얼라이저 유효성 검사 오류 (예: 잘못된 카테고리/장르 형식, 유효하지 않은 URL 등)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        except IntegrityError as e:
            # 데이터베이스 무결성 오류 처리 (예: 중복된 title)

            # 특정 오류 메시지를 기반으로 'title' 중복 오류인지 확인
            if "duplicate key value violates unique constraint" in str(e).lower() and "title" in str(e).lower():
                return Response(
                    {"title": ["이미 동일한 이름의 보드 게임이 등록되어 있습니다."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            logger.error(f"데이터베이스 무결성 오류 발생: {e}", exc_info=True)
            return Response({"detail": "데이터베이스 무결성 오류가 발생했습니다."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # 예상치 못한 기타 서버 오류
            logger.exception("게임 등록 중 예상치 못한 서버 오류 발생")
            return Response({"detail": "서버 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 관리자 보드게임 수정
@extend_schema(
    tags=["[Admin]"],
    summary="관리자 보드 게임 수정",
    description="새로운 보드 게임 정보를 시스템에 수정합니다. title은 고유해야 합니다.",
    request=AdminGameRegisterSerializer,
)
class AdminGameUpdateView(generics.UpdateAPIView[Game]):

    queryset = Game.objects.all()
    serializer_class = AdminGameUpdateSerializer

    permission_classes = [IsAuthenticated, IsAdminRole]

    lookup_field = "game_id"

    def get_object(self) -> Game:

        try:
            game_id_from_url = self.kwargs.get(self.lookup_field)
            return Game.objects.get(game_id=game_id_from_url)
        except Game.DoesNotExist:
            logger.warning(f"게임 ID {game_id_from_url}를 찾을 수 없습니다.")
            raise NotFound(
                {"error": "NOT_FOUND", "message": f"해당 ID({game_id_from_url})의 보드 게임을 찾을 수 없습니다."}
            )

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:

        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            # 데이터베이스에 변경 사항 저장
            self.perform_update(serializer)
            logger.info(f"게임 ID {instance.game_id} 정보가 성공적으로 수정되었습니다.")
        except IntegrityError as e:
            # 데이터베이스 무결성 오류 (예: Unique constraint 위반 등)
            logger.error(f"게임 ID {instance.game_id} 업데이트 중 데이터베이스 무결성 오류: {e}")
            raise ValidationError(
                {  # 400 Bad Request (VALIDATION_ERROR)
                    "error": "VALIDATION_ERROR",
                    "message": "데이터베이스 무결성 오류가 발생했습니다. 중복된 값이 있거나 데이터 형식이 올바르지 않을 수 있습니다.",
                }
            )
        # 500 Internal Server Error 처리 로직은 여기서 제거됩니다.
        # 다른 모든 예상치 못한 예외는 DRF의 기본 핸들러로 넘어갑니다.

        # API 명세서에 맞는 커스텀 성공 응답 데이터 구성
        response_data = {
            "id": instance.game_id,
            "message": "보드 게임 정보가 성공적으로 수정되었습니다.",
            "data": serializer.data,
        }

        # HTTP 200 OK 상태 코드와 함께 커스텀 응답 반환
        return Response(response_data, status=status.HTTP_200_OK)

    def handle_exception(self, exc: Exception) -> Response:
        if isinstance(exc, AuthenticationFailed):
            logger.warning(f"인증 실패: {exc.detail}")
            return Response(
                {"error": "UNAUTHORIZED", "message": "유효한 인증 토큰이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        elif isinstance(exc, PermissionDenied):
            logger.warning(f"권한 없음: {exc.detail}")
            return Response(
                {"error": "FORBIDDEN", "message": "보드 게임을 수정할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif isinstance(exc, NotFound):
            logger.warning(f"리소스 찾을 수 없음: {exc.detail}")
            return Response(exc.detail, status=status.HTTP_404_NOT_FOUND)
        elif isinstance(exc, ValidationError):
            # Initialize with a default generic validation error response
            error_response_data: dict[str, str] = {
                "error": "VALIDATION_ERROR",
                "message": "요청 데이터가 유효하지 않습니다.",
            }

            # Check if exc.detail is a dictionary, as per our custom ValidationError format
            if isinstance(exc.detail, dict):
                # Case 1: Custom error format (e.g., {"error": "DUPLICATE_TITLE", "message": "..."})
                # Ensure both are strings before assigning
                if (
                    "error" in exc.detail
                    and "message" in exc.detail
                    and isinstance(exc.detail["error"], str)
                    and isinstance(exc.detail["message"], str)
                ):
                    # Safely assign if the original detail matches the desired string-string dict type
                    error_response_data["error"] = exc.detail["error"]
                    error_response_data["message"] = exc.detail["message"]
                else:
                    # Case 2: DRF's standard field errors (e.g., {"field_name": ["Error msg 1"]})
                    # Extract the first field's first error message
                    for field_name, errors in exc.detail.items():
                        if isinstance(errors, list) and errors:
                            error_response_data["message"] = str(errors[0])
                            break  # Take the first error from the first field and break
                        elif isinstance(errors, str):  # Handle cases like {"field_name": "Error msg"}
                            error_response_data["message"] = errors
                            break
                    else:  # No errors found in dictionary format (e.g., empty dict)
                        error_response_data["message"] = str(exc.detail)  # Convert entire dict to string
            # Case 3: exc.detail is a list of non-field errors (e.g., ["Global error msg"])
            elif isinstance(exc.detail, list) and exc.detail:
                error_response_data["message"] = str(exc.detail[0])
            # Case 4: Other unexpected formats for exc.detail
            else:
                error_response_data["message"] = str(exc.detail)  # Convert anything else to string

            # Determine status code based on the 'error' key
            if error_response_data.get("error") == "DUPLICATE_TITLE":
                logger.warning(f"데이터 충돌 (Title 중복): {error_response_data.get('message')}")
                return Response(error_response_data, status=status.HTTP_409_CONFLICT)
            else:
                logger.warning(f"요청 데이터 유효성 검사 실패: {error_response_data.get('message')}")
                return Response(error_response_data, status=status.HTTP_400_BAD_REQUEST)

        logger.error(f"처리되지 않은 예외 발생: {type(exc).__name__} - {exc}", exc_info=True)
        return super().handle_exception(exc)


# 관리자 보드게임 삭제
@extend_schema(
    tags=["[Admin]"],
    summary="관리자 보드 게임 삭제",
    description="새로운 보드 게임 정보를 시스템에 삭제합니다. 싼네일 유알엘 먼저 삭제합니다.",
    request=AdminGameRegisterSerializer,
)
class AdminGameDeleteView(generics.DestroyAPIView[Game]):

    queryset = Game.objects.all()  # Game 모델의 모든 객체를 대상으로 합니다.

    # 권한 설정: 인증된 사용자이면서 관리자(IsAdminUser)만 접근 허용
    permission_classes = [IsAuthenticated, IsAdminRole]

    lookup_field = "game_id"

    def get_object(self) -> Game:

        try:
            game_id_from_url = self.kwargs.get(self.lookup_field)
            logger.info(f"게임 삭제 요청: game_id={game_id_from_url}")
            return Game.objects.get(game_id=game_id_from_url)
        except Game.DoesNotExist:
            logger.warning(f"삭제하려는 게임 ID {game_id_from_url}를 찾을 수 없습니다.")
            raise NotFound(
                {"error": "NOT_FOUND", "message": f"해당 ID({game_id_from_url})의 보드 게임을 찾을 수 없습니다."}
            )

    # 게임 객체 삭제를 수행합니다. 게임 삭제 전에 연결된 S3 썸네일 이미지를 삭제합니다.
    def perform_destroy(self, instance: Game) -> None:

        s3_uploader = S3Uploader()
        thumbnail_url_to_delete = instance.thumbnail_url

        # S3 썸네일 URL이 존재하면 S3에서 파일 삭제 시도
        if thumbnail_url_to_delete:
            try:
                # S3Uploader의 delete_file 메서드는 URL을 직접 받습니다.
                s3_uploader.delete_file(thumbnail_url_to_delete)
                logger.info(f"게임 ID {instance.game_id}의 S3 썸네일 파일({thumbnail_url_to_delete}) 삭제 성공.")
            except Exception as e:
                # S3 삭제 실패는 게임 삭제를 막지 않지만, 로그로 기록하여 추후 확인 필요
                logger.error(f"게임 ID {instance.game_id}의 S3 썸네일 파일 삭제 실패: {e}", exc_info=True)

        # 데이터베이스에서 게임 객체 삭제
        instance.delete()
        logger.info(f"게임 ID {instance.game_id}가 데이터베이스에서 성공적으로 삭제되었습니다.")

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:

        # DELETE 요청을 처리하여 보드 게임을 삭제하고, 커스텀 성공 응답을 반환합니다.

        instance = self.get_object()

        self.perform_destroy(instance)

        # API 명세서에 맞는 커스텀 성공 응답 데이터 구성
        response_data = {
            "id": instance.game_id,
            "message": "보드 게임이 성공적으로 삭제되었습니다.",
        }

        # HTTP 204 No Content (삭제 성공) 또는 200 OK 상태 코드와 함께 응답 반환
        # 여기서는 명세서에 따라 커스텀 메시지를 포함하므로 200 OK가 더 적합합니다.
        return Response(response_data, status=status.HTTP_200_OK)

    def handle_exception(self, exc: Exception) -> Response:

        if isinstance(exc, AuthenticationFailed):
            logger.warning(f"인증 실패: {exc.detail}")
            return Response(
                {"error": "UNAUTHORIZED", "message": "유효한 인증 토큰이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        elif isinstance(exc, PermissionDenied):
            logger.warning(f"권한 없음: {exc.detail}")
            return Response(
                {"error": "FORBIDDEN", "message": "보드 게임을 삭제할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif isinstance(exc, NotFound):
            logger.warning(f"리소스 찾을 수 없음: {exc.detail}")
            return Response(exc.detail, status=status.HTTP_404_NOT_FOUND)
        elif isinstance(exc, ValidationError):
            error_response_data: dict[str, str] = {
                "error": "VALIDATION_ERROR",
                "message": "요청 데이터가 유효하지 않습니다.",
            }

            if isinstance(exc.detail, dict):
                if (
                    "error" in exc.detail
                    and "message" in exc.detail
                    and isinstance(exc.detail["error"], str)
                    and isinstance(exc.detail["message"], str)
                ):
                    error_response_data["error"] = exc.detail["error"]
                    error_response_data["message"] = exc.detail["message"]
                else:
                    for field_name, errors in exc.detail.items():
                        if isinstance(errors, list) and errors:
                            error_response_data["message"] = str(errors[0])
                            break
                        elif isinstance(errors, str):
                            error_response_data["message"] = errors
                            break
                    else:
                        error_response_data["message"] = str(exc.detail)
            elif isinstance(exc.detail, list) and exc.detail:
                error_response_data["message"] = str(exc.detail[0])
            else:
                error_response_data["message"] = str(exc.detail)

            if error_response_data.get("error") == "DUPLICATE_TITLE":
                logger.warning(f"데이터 충돌 (Title 중복): {error_response_data.get('message')}")
                return Response(error_response_data, status=status.HTTP_409_CONFLICT)
            else:
                logger.warning(f"요청 데이터 유효성 검사 실패: {error_response_data.get('message')}")
                return Response(error_response_data, status=status.HTTP_400_BAD_REQUEST)

        logger.error(f"처리되지 않은 예외 발생: {type(exc).__name__} - {exc}", exc_info=True)
        return super().handle_exception(exc)
