from rest_framework import routers
from sims.api.views import ProjectViewSet, SampleViewSet, PoolViewSet,\
    LibraryViewSet, AdapterViewSet, RunViewSet, MachineViewSet, RunPoolViewSet,\
    AdapterDBViewset

router = routers.SimpleRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'samples', SampleViewSet)
router.register(r'pools', PoolViewSet)
router.register(r'libraries', LibraryViewSet)
router.register(r'adapters/(?P<db>[^/.]+)', AdapterViewSet)
router.register(r'adapter_db', AdapterDBViewset)
router.register(r'runs', RunViewSet)
router.register(r'run_pools', RunPoolViewSet)
router.register(r'machines', MachineViewSet)

urlpatterns = router.urls