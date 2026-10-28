from apps.notifications.views import NotificationList
from django.contrib import admin
from django.urls import path,include
from apps.accounts.extra_views import StatementView
from apps.operations.extra_views import AuditList, RiskList
from drf_spectacular.views import SpectacularAPIView,SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from apps.identity.views import RegisterView,MeView
from apps.accounts.views import AccountViewSet,BeneficiaryViewSet
from apps.transfers.views import TransferViewSet
from apps.operations.views import OperationsViewSet
from apps.loans.views import LoanViewSet
from apps.cards.views import CardViewSet
from apps.billing.views import BillViewSet
from apps.investments.views import InvestmentViewSet
from rest_framework.routers import DefaultRouter
router=DefaultRouter()
for prefix,view,base in [('accounts',AccountViewSet,'accounts'),('beneficiaries',BeneficiaryViewSet,'beneficiaries'),('transfers',TransferViewSet,'transfers'),('operations',OperationsViewSet,'operations'),('loans',LoanViewSet,'loans'),('cards',CardViewSet,'cards'),('bills',BillViewSet,'bills'),('investments',InvestmentViewSet,'investments')]: router.register(prefix,view,basename=base)
urlpatterns=[path('',include('apps.portal.urls')),path('api/v1/accounts/<uuid:id>/statement/',StatementView.as_view(),name='account-statement'),path('api/v1/operations/audit/',AuditList.as_view(),name='operations-audit'),path('api/v1/operations/risk/',RiskList.as_view(),name='operations-risk'),path('admin/',admin.site.urls),path('api/v1/notifications/',NotificationList.as_view(),name='notifications-list'),path('api/v1/auth/register/',RegisterView.as_view()),path('api/v1/auth/login/',TokenObtainPairView.as_view()),path('api/v1/auth/refresh/',TokenRefreshView.as_view()),path('api/v1/auth/me/',MeView.as_view()),path('api/v1/',include(router.urls)),path('api/schema/',SpectacularAPIView.as_view(),name='schema'),path('api/docs/',SpectacularSwaggerView.as_view(url_name='schema'),name='swagger-ui')]
