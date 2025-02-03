from django.db import models
from django.conf import settings
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models.profile import Profile  # 이미 정의된 Profile 모델
from ..serializers.profile import ProfileSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from ..models.profile import Profile
from main.models.neighbor import Neighbor
from ..serializers.profile import ProfileSerializer
from django.db.models import Q


class ProfileDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        """
        현재 로그인된 사용자의 프로필만 반환
        """
        return Profile.objects.get(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="현재 사용자 프로필 조회",
        operation_description="현재 로그인된 사용자의 프로필 정보를 반환합니다.",
        responses={200: openapi.Response(description="성공적으로 프로필 반환", schema=ProfileSerializer())}
    )
    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        operation_summary="현재 사용자 프로필 전체 수정",
        operation_description="현재 로그인된 사용자의 프로필 정보를 전체 수정합니다.",
        manual_parameters=[
            openapi.Parameter(
                'blog_name', openapi.IN_FORM, description='블로그 이름', type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'blog_pic', openapi.IN_FORM, description='블로그 사진', type=openapi.TYPE_FILE
            ),
            openapi.Parameter(
                'username', openapi.IN_FORM, description='사용자 이름', type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'user_pic', openapi.IN_FORM, description='프로필 사진', type=openapi.TYPE_FILE
            ),
            openapi.Parameter(
                'intro', openapi.IN_FORM, description='자기소개', type=openapi.TYPE_STRING  # intro 필드 추가
            ),
            openapi.Parameter(
                'neighbor_visibility', openapi.IN_FORM, description="서로이웃 목록 공개 여부", type=openapi.TYPE_BOOLEAN
            )
        ],
        responses={
            200: openapi.Response(description="성공적으로 프로필 전체 수정", schema=ProfileSerializer()),
            400: openapi.Response(description="잘못된 요청"),
        }
    )
    def put(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        operation_summary="현재 사용자 프로필 부분 수정",
        operation_description="현재 로그인된 사용자의 프로필만 부분 수정 가능합니다.",
        manual_parameters=[
            openapi.Parameter(
                'blog_name', openapi.IN_FORM, description='블로그 이름', type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'blog_pic', openapi.IN_FORM, description='블로그 사진', type=openapi.TYPE_FILE
            ),
            openapi.Parameter(
                'username', openapi.IN_FORM, description='사용자 이름', type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'user_pic', openapi.IN_FORM, description='프로필 사진', type=openapi.TYPE_FILE
            ),
            openapi.Parameter(
                'intro', openapi.IN_FORM, description='자기소개', type=openapi.TYPE_STRING  # intro 필드 추가
            ),
        ],
        responses={
            200: openapi.Response(description="성공적으로 프로필 수정", schema=ProfileSerializer())
        }
    )
    def patch(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)



class ProfilePublicView(RetrieveAPIView):
    """
    ✅ 타인의 프로필 조회 (GET /api/profile/{user_id}/)
    - 프로필이 존재하지 않으면 404 반환.
    - 로그인하지 않은 사용자도 조회 가능.
    - 서로이웃 여부(`is_neighbor`)를 추가하여 반환.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # 로그인하지 않아도 조회 가능

    @swagger_auto_schema(
        operation_summary="타인의 프로필 조회",
        operation_description="특정 사용자의 블로그 프로필을 조회합니다. "
                              "현재 로그인한 사용자가 조회 대상과 서로이웃인지 여부(`is_neighbor`)를 함께 반환합니다.",
        manual_parameters=[
            openapi.Parameter(
                name="user_id",
                in_=openapi.IN_PATH,
                description="조회할 사용자의 ID (CustomUser 모델의 Primary Key, 문자열)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="성공적으로 프로필을 반환",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user": openapi.Schema(type=openapi.TYPE_STRING, description="사용자의 ID"),
                        "blog_name": openapi.Schema(type=openapi.TYPE_STRING, description="블로그 이름"),
                        "blog_pic": openapi.Schema(type=openapi.TYPE_STRING, format="url", description="블로그 프로필 이미지 URL"),
                        "username": openapi.Schema(type=openapi.TYPE_STRING, description="사용자 이름"),
                        "user_pic": openapi.Schema(type=openapi.TYPE_STRING, format="url", description="프로필 사진 URL"),
                        "intro": openapi.Schema(type=openapi.TYPE_STRING, description="사용자의 자기소개"),
                        "is_neighbor": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="현재 로그인한 사용자가 조회 대상과 서로이웃인지 여부")
                    }
                )
            ),
            404: openapi.Response(description="해당 사용자의 프로필을 찾을 수 없음")
        }
    )
    def get(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")  # URL에서 user_id 가져오기
        profile = get_object_or_404(Profile, user_id=user_id)  # 해당 user_id의 Profile 가져오기
        serializer = self.get_serializer(profile)

        # ✅ 현재 로그인한 사용자가 서로이웃인지 확인 (status="accepted"인 경우만 체크)
        is_neighbor = False
        if request.user.is_authenticated:
            is_neighbor = Neighbor.objects.filter(
                (Q(from_user=request.user, to_user=profile.user) |
                 Q(from_user=profile.user, to_user=request.user)),
                status="accepted"  # 🔥 서로이웃 수락된 경우만 체크
            ).exists()

        response_data = serializer.data
        response_data["is_neighbor"] = is_neighbor  # ✅ 서로이웃 여부 추가

        return Response(response_data)