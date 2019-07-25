from rest_framework import viewsets
from sims.api.serializers import RunSerializer,RunDetailSerializer, MachineSerializer,\
    ProjectSerializer, SampleSerializer, PoolSerializer, LibrarySerializer,\
    AdapterSerializer, RunPoolSerializer, RunPoolDetailSerializer
from sims.models import Run, Machine, Project, Sample, Pool, Library, Adapter,\
    RunPool
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from sims.submission import Submission

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    filter_fields = {
        'id':['icontains','exact'],
        'samples__id': ['exact'],
        'samples__libraries__id': ['exact'],
        'samples__libraries__pools__id': ['exact'],
        'samples__libraries__pools__run_pools__run__id': ['exact']
        }
    ordering_fields = ['id', 'submitted', 'submission_id']
    queryset = Project.objects.distinct()
    @action(detail=False, methods=['get','post'])
    def import_submission(self, request):
        data = request.query_params
        url = settings.SUBMISSION_SYSTEM_URLS['submission'].format(id=data.get('id'))
        submission = Submission.get_submission(data.get('id'))
        project = submission.create_project()
        return Response({'id':data,'url':url, 'submission':submission._data, 'project': ProjectSerializer(project).data})

class SampleViewSet(viewsets.ModelViewSet):
    filter_fields = {
        'name':['icontains','exact'],
        'id':['icontains','exact'],
        'project__id':['icontains','exact'],
        }
    serializer_class = SampleSerializer
    queryset = Sample.objects.distinct()

class LibraryViewSet(viewsets.ModelViewSet):
    filter_fields = {
        'id':['icontains','exact'],
        'sample__name':['icontains','exact'],
        'sample__id':['icontains','exact'],
        'sample__project__id':['icontains','exact'],
        'pools__id': ['exact'],
        'pools__run_pools__run__id': ['exact']
        }
    serializer_class = LibrarySerializer
    queryset = Library.objects.distinct()

class PoolViewSet(viewsets.ModelViewSet):
    filter_fields = {
        'name':['icontains','exact'],
        'libraries__id':['exact'],
        'libraries__sample__id':['exact'],
        'libraries__sample__project__id':['exact']
        }
    serializer_class = PoolSerializer
    queryset = Pool.objects.distinct()
    @action(detail=True, methods=['get','post'])
    def add_libraries(self, request, pk=None):
        return self.update_libraries(request, 'add')
    @action(detail=True, methods=['get','post'])
    def remove_libraries(self, request, pk=None):
        return self.update_libraries(request, 'remove')
    def update_libraries(self, request, action):
        pool = self.get_object()
        data = request.query_params
        libraries = list(Library.objects.filter(id__in=data.getlist('libraries',[])))
        libraries += list(Library.objects.filter(sample__project__id__in=data.getlist('projects',[])))
        if action == 'add':
            pool.libraries.add(*libraries)
        elif action == 'remove':
            pool.libraries.remove(*libraries)
        return Response({'libraries': LibrarySerializer(pool.libraries.all(),many=True).data})
    @action(detail=True, methods=['get','post'])
    def add_pools(self, request, pk=None):
        return self.update_pools(request, 'add')
    @action(detail=True, methods=['get','post'])
    def remove_pools(self, request, pk=None):
        return self.update_pools(request, 'remove')
    def update_pools(self, request, action):
        pool = self.get_object()
        data = request.query_params
        pools = list(Pool.objects.filter(id__in=data.getlist('pools',[])))
        if action == 'add':
            pool.pools.add(*pools)
        elif action == 'remove':
            pool.pools.remove(*pools)
        return Response({'pools': PoolSerializer(pool.pools.all(),many=True).data})

class AdapterViewSet(viewsets.ModelViewSet):
    filter_fields = {
        'name':['icontains','exact'],
        'barcode':['icontains','exact'],
        'description':['icontains']
        }
    serializer_class = AdapterSerializer
    queryset = Adapter.objects.distinct()
# #@todo: fix this... it isn't being called when used as a mixin
# class ActionSerializerMixin(object):
#     """
#     Provide the following in model for different serializers
#     action_serializers = {
#         'retrieve': MyModelDetailSerializer,
#         'list': MyModelListSerializer,
#         'create': MyModelCreateSerializer
#     }
#     """
#     def get_serializer_class(self):
#         if hasattr(self, 'action_serializers'):
#             if self.action in self.action_serializers.keys():
#                 return self.action_serializers[self.action]
#         return viewsets.ModelViewSet.get_serializer_class(self)


class RunViewSet(viewsets.ModelViewSet):
    action_serializers = {
        'retrieve': RunDetailSerializer,
        'list': RunSerializer,
        'create': RunSerializer,
        'update': RunSerializer
    }
    serializer_class = RunSerializer
    queryset = Run.objects.distinct()
    filter_fields = {
        'name':['icontains'],
        'machine__id':['exact'],
        'machine__name':['icontains'],
        'description':['icontains'],
        'run_pools__pool__id':['exact'],
        'run_pools__pool__libraries__id':['exact'],
        'run_pools__pool__libraries__sample__id':['exact'],
        'run_pools__pool__libraries__sample__project__id':['exact'],
        }#,'lanes__pool__library__name':['icontains'],'lanes__pool__name':['icontains']
    def get_queryset(self):
        if self.action == 'retrieve':
            return Run.objects.distinct().prefetch_related('run_pools', 'run_pools__pool__libraries')
        return Run.objects.distinct()
    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers.keys():
                return self.action_serializers[self.action]
        return viewsets.ModelViewSet.get_serializer_class(self)

class RunPoolViewSet(viewsets.ModelViewSet):
    filter_fields = {'run__id':['exact']}
    serializer_class = RunPoolSerializer
    queryset = RunPool.objects.distinct()
    action_serializers = {
        'retrieve': RunPoolDetailSerializer,
        'list': RunPoolSerializer,
        'create': RunPoolSerializer,
        'update': RunPoolSerializer
    }
    def get_queryset(self):
        if self.action == 'retrieve':
            return RunPool.objects.distinct().prefetch_related('pool__libraries')
        return RunPool.objects.distinct()
    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers.keys():
                return self.action_serializers[self.action]
        return viewsets.ModelViewSet.get_serializer_class(self)

class MachineViewSet(viewsets.ModelViewSet):
    serializer_class = MachineSerializer
    model = Machine
    filter_fields = {'name':['icontains'],'description':['icontains']}
#     filter_fields = {'machine__name':['icontains'],'description':['icontains']}#,'lanes__pool__library__name':['icontains'],'lanes__pool__name':['icontains']
    queryset = Machine.objects.distinct()
