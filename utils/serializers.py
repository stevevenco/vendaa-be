from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        lookup_fields = "pk"
        read_only_fields = ("pk", "uuid")
        extra_kwargs = {
            "url": {"lookup_field": ("pk")},
        }
