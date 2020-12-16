from rest_framework import filters


class IsOwnerFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(user=request.user)


class TagsFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        tags = request.query_params.get("tags", None)

        if tags:
            tags = tags.split(",")
            queryset = queryset.filter(tags__name__in=tags).distinct()

        return queryset