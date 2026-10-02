from django.contrib.auth.models import User
from rest_framework import serializers

from advertisements.models import Advertisement, AdvertisementStatusChoices


class UserSerializer(serializers.ModelSerializer):
    """Serializer для пользователя."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name',)


class AdvertisementSerializer(serializers.ModelSerializer):
    """Serializer для объявления."""

    creator = UserSerializer(
        read_only=True,
    )

    class Meta:
        model = Advertisement
        fields = ('id', 'title', 'description', 'creator',
                  'status', 'created_at', )

    def create(self, validated_data):
        """Метод для создания"""

        # Простановка значения поля создатель по-умолчанию.
        # Текущий пользователь является создателем объявления
        # изменить или переопределить его через API нельзя.
        # обратите внимание на `context` – он выставляется автоматически
        # через методы ViewSet.
        # само поле при этом объявляется как `read_only=True`
        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):
        """Метод для валидации. Вызывается при создании и обновлении."""

        request = self.context["request"]
        status = data.get("status")

        if self.instance:
            creator = self.instance.creator
            status = status or self.instance.status
        else:
            creator = request.user
            status = status or AdvertisementStatusChoices.OPEN

        if status == AdvertisementStatusChoices.OPEN:
            open_advertisements = Advertisement.objects.filter(
                creator=creator,
                status=AdvertisementStatusChoices.OPEN,
            )

            if self.instance:
                open_advertisements = open_advertisements.exclude(
                    pk=self.instance.pk,
                )

            if open_advertisements.count() >= 10:
                raise serializers.ValidationError(
                    "У пользователя не может быть больше 10 открытых объявлений."
                )

        return data
