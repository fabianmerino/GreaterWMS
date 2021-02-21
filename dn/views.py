from rest_framework import viewsets
from .models import DnListModel, DnDetailModel, PickingListModel
from . import serializers
from .page import MyPageNumberPaginationDNList
from utils.page import MyPageNumberPagination
from utils.datasolve import sumOfList, transportation_calculate
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from .filter import DnListFilter, DnDetailFilter, DnPickingListFilter
from rest_framework.exceptions import APIException
from customer.models import ListModel as customer
from warehouse.models import ListModel as warehouse
from goods.models import ListModel as goods
from payment.models import TransportationFeeListModel as transportation
from stock.models import StockListModel as stocklist
from stock.models import StockBinModel as stockbin
from driver.models import ListModel as driverlist
from driver.models import DispatchListModel as driverdispatch
from django.db.models import Q
import re
from .serializers import FileListRenderSerializer, FileDetailRenderSerializer
from django.http import StreamingHttpResponse
from .files import FileListRenderCN, FileListRenderEN, FileDetailRenderCN, FileDetailRenderEN
from rest_framework.settings import api_settings

class DnListViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）

        list:
            Response a data list（all）

        create:
            Create a data line（post）

        delete:
            Delete a data line（delete)

    """
    queryset = DnListModel.objects.all()
    serializer_class = serializers.DNListGetSerializer
    pagination_class = MyPageNumberPaginationDNList
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            if id is None:
                return self.queryset.filter(openid=self.request.auth.openid, is_delete=False)
            else:
                return self.queryset.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return self.queryset.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.DNListGetSerializer
        elif self.action == 'retrieve':
            return serializers.DNListGetSerializer
        elif self.action == 'create':
            return serializers.DNListPostSerializer
        elif self.action == 'update':
            return serializers.DNListUpdateSerializer
        elif self.action == 'partial_update':
            return serializers.DNListPartialUpdateSerializer
        elif self.action == 'destroy':
            return serializers.DNListGetSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, *args, **kwargs):
        data = request.data
        data['openid'] = self.request.auth.openid
        if self.queryset.filter(openid=data['openid'], is_delete=False).exists():
            dn_last_code = self.queryset.filter(openid=data['openid']).first().dn_code
            dn_add_code = str(int(re.findall(r'\d+', str(dn_last_code), re.IGNORECASE)[0]) + 1).zfill(8)
            data['dn_code'] = 'DN' + dn_add_code
        else:
            data['dn_code'] = 'DN00000001'
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=200, headers=headers)

    def destroy(self, request, pk):
        qs = self.get_object()
        if qs.openid != self.request.auth.openid:
            raise APIException({"detail": "Cannot delete data which not yours"})
        else:
            if qs.dn_status == 1:
                qs.is_delete = True
                dn_detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid, dn_code=qs.dn_code,
                                              dn_status=1, is_delete=False)
                for i in range(len(dn_detail_list)):
                    goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                goods_code=str(dn_detail_list[i].goods_code)).first()
                    goods_qty_change.dn_stock = goods_qty_change.dn_stock - int(dn_detail_list[i].goods_qty)
                    goods_qty_change.save()
                dn_detail_list.update(is_delete=True)
                qs.save()
                serializer = self.get_serializer(qs, many=False)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=200, headers=headers)
            else:
                raise APIException({"detail": "This order has Confirmed or Deliveried"})

class DnDetailViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）

        list:
            Response a data list（all）

        create:
            Create a data line（post）

        update:
            Update a data（put：update）
    """
    queryset = DnDetailModel.objects.all()
    serializer_class = serializers.DNDetailGetSerializer
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnDetailFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            if id is None:
                return self.queryset.filter(openid=self.request.auth.openid, is_delete=False)
            else:
                return self.queryset.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return self.queryset.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.DNDetailGetSerializer
        elif self.action == 'retrieve':
            return serializers.DNDetailGetSerializer
        elif self.action == 'create':
            return serializers.DNDetailPostSerializer
        elif self.action == 'update':
            return serializers.DNDetailUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, *args, **kwargs):
        data = request.data
        if DnListModel.objects.filter(openid=self.request.auth.openid, dn_code=str(data['dn_code']), is_delete=False).exists():
            if customer.objects.filter(openid=self.request.auth.openid, customer_name=str(data['customer']), is_delete=False).exists():
                for i in range(len(data['goods_code'])):
                    check_data = {
                        'openid': self.request.auth.openid,
                        'dn_code': str(data['dn_code']),
                        'customer': str(data['customer']),
                        'goods_code': str(data['goods_code'][i]),
                        'goods_qty': int(data['goods_qty'][i]),
                        'creater': str(data['creater'])
                    }
                    serializer = self.get_serializer(data=check_data)
                    serializer.is_valid(raise_exception=True)
                post_data_list = []
                weight_list = []
                volume_list = []
                for j in range(len(data['goods_code'])):
                    goods_detail = goods.objects.filter(openid=self.request.auth.openid,
                                                        goods_code=str(data['goods_code'][j]),
                                                        is_delete=False).first()
                    goods_weight = round(goods_detail.goods_weight * int(data['goods_qty'][j]) / 1000, 4)
                    goods_volume = round(goods_detail.unit_volume * int(data['goods_qty'][j]), 4)
                    if stocklist.objects.filter(openid=self.request.auth.openid, goods_code=str(data['goods_code'][j]),
                                                can_order_stock__gte=0).exists():
                        goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                    goods_code=str(data['goods_code'][j])).first()
                        goods_qty_change.dn_stock = goods_qty_change.dn_stock + int(data['goods_qty'][j])
                        goods_qty_change.save()
                    else:
                        stocklist.objects.create(openid=self.request.auth.openid,
                                                 goods_code=str(data['goods_code'][j]),
                                                 goods_desc=goods_detail.goods_desc,
                                                 dn_stock=int(data['goods_qty'][j]))
                    post_data = DnDetailModel(openid=self.request.auth.openid,
                                              dn_code=str(data['dn_code']),
                                              customer=str(data['customer']),
                                              goods_code=str(data['goods_code'][j]),
                                              goods_qty=int(data['goods_qty'][j]),
                                              goods_weight=goods_weight,
                                              goods_volume=goods_volume,
                                              creater=str(data['creater']))
                    weight_list.append(goods_weight)
                    volume_list.append(goods_volume)
                    post_data_list.append(post_data)
                total_weight = sumOfList(weight_list, len(weight_list))
                total_volume = sumOfList(volume_list, len(volume_list))
                customer_city = customer.objects.filter(openid=self.request.auth.openid,
                                                        customer_name=str(data['customer']),
                                                        is_delete=False).first().customer_city
                warehouse_city = warehouse.objects.filter(openid=self.request.auth.openid).first().warehouse_city
                transportation_fee = transportation.objects.filter(
                    Q(openid=self.request.auth.openid, send_city__icontains=warehouse_city, receiver_city__icontains=customer_city,
                      is_delete=False) | Q(openid='init_data', send_city__icontains=warehouse_city, receiver_city__icontains=customer_city,
                                           is_delete=False))
                transportation_res = {
                    "detail": []
                }
                if len(transportation_fee) >= 1:
                    transportation_list = []
                    for k in range(len(transportation_fee)):
                        transportation_cost = transportation_calculate(total_weight,
                                                                       total_volume,
                                                                       transportation_fee[k].weight_fee,
                                                                       transportation_fee[k].volume_fee,
                                                                       transportation_fee[k].min_payment)
                        transportation_detail = {
                            "transportation_supplier": transportation_fee[k].transportation_supplier,
                            "transportation_cost": transportation_cost
                        }
                        transportation_list.append(transportation_detail)
                    transportation_res['detail'] = transportation_list
                DnDetailModel.objects.bulk_create(post_data_list, batch_size=100)
                DnListModel.objects.filter(openid=self.request.auth.openid, dn_code=str(data['dn_code'])).update(
                    customer=str(data['customer']), total_weight=total_weight, total_volume=total_volume,
                    transportation_fee=transportation_res)
                return Response({"success": "Yes"}, status=200)
            else:
                raise APIException({"detail": "customer does not exists"})
        else:
            raise APIException({"detail": "DN Code does not exists"})

    def update(self, request, *args, **kwargs):
        data = request.data
        if DnListModel.objects.filter(openid=self.request.auth.openid, dn_code=str(data['dn_code']),
                                       dn_status=1, is_delete=False).exists():
            if customer.objects.filter(openid=self.request.auth.openid, customer_name=str(data['customer']),
                                       is_delete=False).exists():
                for i in range(len(data['goods_code'])):
                    check_data = {
                        'openid': self.request.auth.openid,
                        'dn_code': str(data['dn_code']),
                        'customer': str(data['customer']),
                        'goods_code': str(data['goods_code'][i]),
                        'goods_qty': int(data['goods_qty'][i]),
                        'creater': str(data['creater'])
                    }
                    serializer = self.get_serializer(data=check_data)
                    serializer.is_valid(raise_exception=True)
                dn_detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                              dn_code=str(data['dn_code']))
                for v in range(len(dn_detail_list)):
                    goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                goods_code=str(dn_detail_list[v].goods_code)).first()
                    goods_qty_change.dn_stock = goods_qty_change.dn_stock - dn_detail_list[v].goods_qty
                    if goods_qty_change.dn_stock < 0:
                        goods_qty_change.dn_stock = 0
                    goods_qty_change.save()
                    dn_detail_list[v].is_delete = True
                    dn_detail_list[v].save()
                post_data_list = []
                weight_list = []
                volume_list = []
                for j in range(len(data['goods_code'])):
                    goods_detail = goods.objects.filter(openid=self.request.auth.openid,
                                                        goods_code=str(data['goods_code'][j]),
                                                        is_delete=False).first()
                    goods_weight = round(goods_detail.goods_weight * int(data['goods_qty'][j]) / 1000, 4)
                    goods_volume = round(goods_detail.unit_volume * int(data['goods_qty'][j]), 4)
                    if stocklist.objects.filter(openid=self.request.auth.openid, goods_code=str(data['goods_code'][j]),
                                                can_order_stock__gt=0).exists():
                        goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                    goods_code=str(data['goods_code'][j])).first()
                        goods_qty_change.dn_stock = goods_qty_change.dn_stock + int(data['goods_qty'][j])
                        goods_qty_change.save()
                    else:
                        stocklist.objects.create(openid=self.request.auth.openid,
                                                 goods_code=str(data['goods_code'][j]),
                                                 goods_desc=goods_detail.goods_desc,
                                                 dn_stock=int(data['goods_qty'][j]))
                    post_data = DnDetailModel(openid=self.request.auth.openid,
                                              dn_code=str(data['dn_code']),
                                              customer=str(data['customer']),
                                              goods_code=str(data['goods_code'][j]),
                                              goods_qty=int(data['goods_qty'][j]),
                                              goods_weight=goods_weight,
                                              goods_volume=goods_volume,
                                              creater=str(data['creater']))
                    weight_list.append(goods_weight)
                    volume_list.append(goods_volume)
                    post_data_list.append(post_data)
                total_weight = sumOfList(weight_list, len(weight_list))
                total_volume = sumOfList(volume_list, len(volume_list))
                customer_city = customer.objects.filter(openid=self.request.auth.openid,
                                                        customer_name=str(data['customer']),
                                                        is_delete=False).first().customer_city
                warehouse_city = warehouse.objects.filter(openid=self.request.auth.openid).first().warehouse_city
                transportation_fee = transportation.objects.filter(
                    Q(openid=self.request.auth.openid, send_city__icontains=warehouse_city,
                      receiver_city__icontains=customer_city,
                      is_delete=False) | Q(openid='init_data', send_city__icontains=warehouse_city,
                                           receiver_city__icontains=customer_city,
                                           is_delete=False))
                transportation_res = {
                    "detail": []
                }
                if len(transportation_fee) >= 1:
                    transportation_list = []
                    for k in range(len(transportation_fee)):
                        transportation_cost = transportation_calculate(total_weight,
                                                                       total_volume,
                                                                       transportation_fee[k].weight_fee,
                                                                       transportation_fee[k].volume_fee,
                                                                       transportation_fee[k].min_payment)
                        transportation_detail = {
                            "transportation_supplier": transportation_fee[k].transportation_supplier,
                            "transportation_cost": transportation_cost
                        }
                        transportation_list.append(transportation_detail)
                    transportation_res['detail'] = transportation_list
                DnDetailModel.objects.bulk_create(post_data_list, batch_size=100)
                DnListModel.objects.filter(openid=self.request.auth.openid, dn_code=str(data['dn_code'])).update(
                    customer=str(data['customer']), total_weight=total_weight, total_volume=total_volume,
                    transportation_fee=transportation_res)
                return Response({"success": "Yes"}, status=200)
            else:
                raise APIException({"detail": "Customer does not exists"})
        else:
            raise APIException({"detail": "DN Code has been Confirmed or does not exists"})

class DnViewPrintViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）
    """
    queryset = DnListModel.objects.all()
    serializer_class = serializers.DNListGetSerializer
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            if id is None:
                return self.queryset.filter(openid=self.request.auth.openid, is_delete=False)
            else:
                return self.queryset.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return self.queryset.none()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.DNDetailGetSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def retrieve(self, request, pk):
        qs = self.get_object()
        if qs.openid != self.request.auth.openid:
            raise APIException({"detail": "Cannot update data which not yours"})
        else:
            context = {}
            dn_detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                                            dn_code=qs.dn_code)
            dn_detail = serializers.DNDetailGetSerializer(dn_detail_list, many=True)
            customer_detail = customer.objects.filter(openid=self.request.auth.openid,
                                                            customer_name=qs.customer).first()
            warehouse_detail = warehouse.objects.filter(openid=self.request.auth.openid).first()
            context['dn_detail'] = dn_detail.data
            context['customer_detail'] = {
                "customer_name": customer_detail.customer_name,
                "customer_city": customer_detail.customer_city,
                "customer_address": customer_detail.customer_address,
                "customer_contact": customer_detail.customer_contact
            }
            context['warehouse_detail'] = {
                "warehouse_name": warehouse_detail.warehouse_name,
                "warehouse_city": warehouse_detail.warehouse_city,
                "warehouse_address": warehouse_detail.warehouse_address,
                "warehouse_contact": warehouse_detail.warehouse_contact
            }
        return Response(context, status=200)

class DnNewOrderViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）
    """
    queryset = DnListModel.objects.all()
    serializer_class = serializers.DNListGetSerializer
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            if id is None:
                return self.queryset.filter(openid=self.request.auth.openid, is_delete=False)
            else:
                return self.queryset.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return self.queryset.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.DNListPartialUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, pk):
        qs = self.get_object()
        if qs.openid != self.request.auth.openid:
            raise APIException({"detail": "Cannot delete data which not yours"})
        else:
            if qs.dn_status == 1:
                qs.dn_status = 2
                dn_detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid, dn_code=qs.dn_code,
                                                                dn_status=1, is_delete=False)
                for i in range(len(dn_detail_list)):
                    goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                goods_code=str(dn_detail_list[i].goods_code)).first()
                    goods_qty_change.can_order_stock = goods_qty_change.can_order_stock - dn_detail_list[i].goods_qty
                    goods_qty_change.ordered_stock = goods_qty_change.ordered_stock + dn_detail_list[i].goods_qty
                    goods_qty_change.dn_stock = goods_qty_change.dn_stock - dn_detail_list[i].goods_qty
                    if goods_qty_change.can_order_stock < 0:
                        goods_qty_change.can_order_stock = 0
                    goods_qty_change.save()
                dn_detail_list.update(dn_status=2)
                qs.save()
                serializer = self.get_serializer(qs, many=False)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=200, headers=headers)
            else:
                raise APIException({"detail": "This order status has been changed can not be edit"})

class DnOrderReleaseViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Response a data list（get）
    """
    queryset = DnListModel.objects.all()
    serializer_class = serializers.DNListGetSerializer
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            if id is None:
                return self.queryset.filter(openid=self.request.auth.openid, dn_status=2, is_delete=False).order_by('create_time')
            else:
                return self.queryset.filter(openid=self.request.auth.openid, dn_status=2, id=id, is_delete=False)
        else:
            return self.queryset.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.DNListUpdateSerializer
        elif self.action == 'update':
            return serializers.DNListUpdateSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, *args, **kwargs):
        qs = self.get_queryset()
        for v in range(len(qs)):
            dn_detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid, dn_code=qs[v].dn_code,
                                                          dn_status=2, is_delete=False)
            picking_list = []
            picking_list_label = 0
            back_order_list = []
            back_order_list_label = 0
            back_order_goods_weight_list = []
            back_order_goods_volume_list = []
            back_order_base_code = DnListModel.objects.filter(openid=self.request.auth.openid,
                                                              is_delete=False).order_by('-id').first().dn_code
            dn_last_code = re.findall(r'\d+', str(back_order_base_code), re.IGNORECASE)
            back_order_dn_code = 'DN' + str(int(dn_last_code[0]) + 1).zfill(8)
            total_weight = qs[v].total_weight
            total_volume = qs[v].total_volume
            for i in range(len(dn_detail_list)):
                goods_detail = goods.objects.filter(openid=self.request.auth.openid,
                                                    goods_code=str(dn_detail_list[i].goods_code),
                                                    is_delete=False).first()
                if stocklist.objects.filter(openid=self.request.auth.openid,
                                            goods_code=str(dn_detail_list[i].goods_code)).exists():
                    pass
                else:
                    stocklist.objects.create(openid=self.request.auth.openid,
                                             goods_code=str(goods_detail.goods_code),
                                             goods_desc=goods_detail.goods_desc,
                                             dn_stock=int(dn_detail_list[i].goods_qty))
                goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                            goods_code=str(
                                                                dn_detail_list[i].goods_code)).first()
                goods_bin_stock_list = stockbin.objects.filter(openid=self.request.auth.openid,
                                                               goods_code=str(dn_detail_list[i].goods_code),
                                                               bin_property="Normal").order_by('-id')
                can_pick_qty = goods_qty_change.onhand_stock - \
                               goods_qty_change.inspect_stock - \
                               goods_qty_change.hold_stock - \
                               goods_qty_change.damage_stock - \
                               goods_qty_change.pick_stock - \
                               goods_qty_change.picked_stock
                if can_pick_qty > 0:
                    if dn_detail_list[i].goods_qty > can_pick_qty:
                        if qs[v].back_order_label == False:
                            dn_pick_qty = dn_detail_list[i].pick_qty
                            for j in range(len(goods_bin_stock_list)):
                                bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - \
                                                   goods_bin_stock_list[j].pick_qty - \
                                                   goods_bin_stock_list[j].picked_qty
                                if bin_can_pick_qty > 0:
                                    goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                           j].pick_qty + bin_can_pick_qty
                                    goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                    goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                    picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                         dn_code=dn_detail_list[i].dn_code,
                                                                         bin_name=goods_bin_stock_list[j].bin_name,
                                                                         goods_code=goods_bin_stock_list[
                                                                             i].goods_code,
                                                                         pick_qty=bin_can_pick_qty,
                                                                         creater=self.request.auth.name))
                                    picking_list_label = 1
                                    dn_pick_qty = dn_pick_qty + bin_can_pick_qty
                                    goods_qty_change.save()
                                    goods_bin_stock_list[j].save()
                                elif bin_can_pick_qty == 0:
                                    continue
                                else:
                                    continue
                            dn_detail_list[i].pick_qty = dn_pick_qty
                            dn_back_order_qty = dn_detail_list[i].goods_qty - \
                                                dn_detail_list[i].pick_qty - \
                                                dn_detail_list[i].picked_qty
                            dn_detail_list[i].goods_qty = dn_pick_qty
                            dn_detail_list[i].dn_status = 3
                            goods_qty_change.back_order_stock = goods_qty_change.back_order_stock + \
                                                                dn_back_order_qty
                            back_order_goods_volume = round(goods_detail.unit_volume * dn_back_order_qty, 4)
                            back_order_goods_weight = round(
                                (goods_detail.goods_weight * dn_back_order_qty) / 1000, 4)
                            back_order_list.append(DnDetailModel(dn_code=back_order_dn_code,
                                                                 dn_status=2,
                                                                 customer=qs[v].customer,
                                                                 goods_code=dn_detail_list[i].goods_code,
                                                                 goods_qty=dn_back_order_qty,
                                                                 goods_weight=back_order_goods_weight,
                                                                 goods_volume=back_order_goods_volume,
                                                                 creater=self.request.auth.name,
                                                                 back_order_label=True,
                                                                 openid=self.request.auth.openid,
                                                                 create_time=dn_detail_list[i].create_time))
                            back_order_list_label = 1
                            total_weight = total_weight - back_order_goods_weight
                            total_volume = total_volume - back_order_goods_volume
                            dn_detail_list[i].goods_weight = dn_detail_list[i].goods_weight - \
                                                             back_order_goods_weight
                            dn_detail_list[i].goods_volume = dn_detail_list[i].goods_volume - \
                                                             back_order_goods_volume
                            back_order_goods_weight_list.append(back_order_goods_weight)
                            back_order_goods_volume_list.append(back_order_goods_volume)
                            goods_qty_change.save()
                            dn_detail_list[i].save()
                        else:
                            dn_pick_qty = dn_detail_list[i].pick_qty
                            for j in range(len(goods_bin_stock_list)):
                                bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - \
                                                   goods_bin_stock_list[j].pick_qty - \
                                                   goods_bin_stock_list[j].picked_qty
                                if bin_can_pick_qty > 0:
                                    goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                           j].pick_qty + bin_can_pick_qty
                                    goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                    goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                    picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                         dn_code=dn_detail_list[i].dn_code,
                                                                         bin_name=goods_bin_stock_list[j].bin_name,
                                                                         goods_code=goods_bin_stock_list[
                                                                             i].goods_code,
                                                                         pick_qty=bin_can_pick_qty,
                                                                         creater=self.request.auth.name))
                                    picking_list_label = 1
                                    dn_pick_qty = dn_pick_qty + bin_can_pick_qty
                                    goods_qty_change.save()
                                    goods_bin_stock_list[j].save()
                                elif bin_can_pick_qty == 0:
                                    continue
                                else:
                                    continue
                            dn_detail_list[i].pick_qty = dn_pick_qty
                            dn_back_order_qty = dn_detail_list[i].goods_qty - \
                                                dn_detail_list[i].pick_qty - \
                                                dn_detail_list[i].picked_qty
                            dn_detail_list[i].goods_qty = dn_pick_qty
                            dn_detail_list[i].dn_status = 3
                            back_order_goods_volume = round(goods_detail.unit_volume * dn_back_order_qty, 4)
                            back_order_goods_weight = round(
                                (goods_detail.goods_weight * dn_back_order_qty) / 1000, 4)
                            back_order_list.append(DnDetailModel(dn_code=back_order_dn_code,
                                                                 dn_status=2,
                                                                 customer=qs[v].customer,
                                                                 goods_code=dn_detail_list[i].goods_code,
                                                                 goods_qty=dn_back_order_qty,
                                                                 goods_weight=back_order_goods_weight,
                                                                 goods_volume=back_order_goods_volume,
                                                                 creater=self.request.auth.name,
                                                                 back_order_label=True,
                                                                 openid=self.request.auth.openid,
                                                                 create_time=dn_detail_list[i].create_time))
                            back_order_list_label = 1
                            total_weight = total_weight - back_order_goods_weight
                            total_volume = total_volume - back_order_goods_volume
                            dn_detail_list[i].goods_weight = dn_detail_list[i].goods_weight - \
                                                             back_order_goods_weight
                            dn_detail_list[i].goods_volume = dn_detail_list[i].goods_volume - \
                                                             back_order_goods_volume
                            back_order_goods_weight_list.append(back_order_goods_weight)
                            back_order_goods_volume_list.append(back_order_goods_volume)
                            dn_detail_list[i].save()
                    elif dn_detail_list[i].goods_qty == can_pick_qty:
                        for j in range(len(goods_bin_stock_list)):
                            bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - goods_bin_stock_list[
                                j].pick_qty - \
                                               goods_bin_stock_list[j].picked_qty
                            if bin_can_pick_qty > 0:
                                dn_need_pick_qty = dn_detail_list[i].goods_qty - dn_detail_list[i].pick_qty - \
                                                   dn_detail_list[i].picked_qty
                                if dn_need_pick_qty > bin_can_pick_qty:
                                    goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                           j].pick_qty + bin_can_pick_qty
                                    goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                    goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                    picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                         dn_code=dn_detail_list[i].dn_code,
                                                                         bin_name=goods_bin_stock_list[j].bin_name,
                                                                         goods_code=goods_bin_stock_list[
                                                                             i].goods_code,
                                                                         pick_qty=bin_can_pick_qty,
                                                                         creater=self.request.auth.name))
                                    picking_list_label = 1
                                    dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + bin_can_pick_qty
                                    goods_bin_stock_list[j].save()
                                    goods_qty_change.save()
                                elif dn_need_pick_qty == bin_can_pick_qty:
                                    goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                           j].pick_qty + bin_can_pick_qty
                                    goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                    goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                    picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                         dn_code=dn_detail_list[i].dn_code,
                                                                         bin_name=goods_bin_stock_list[j].bin_name,
                                                                         goods_code=goods_bin_stock_list[
                                                                             i].goods_code,
                                                                         pick_qty=bin_can_pick_qty,
                                                                         creater=self.request.auth.name))
                                    picking_list_label = 1
                                    dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + bin_can_pick_qty
                                    dn_detail_list[i].dn_status = 3
                                    dn_detail_list[i].save()
                                    goods_bin_stock_list[j].save()
                                    goods_qty_change.save()
                                    break
                                else:
                                    break
                            elif bin_can_pick_qty == 0:
                                continue
                            else:
                                continue
                    elif dn_detail_list[i].goods_qty < can_pick_qty:
                        for j in range(len(goods_bin_stock_list)):
                            bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - \
                                               goods_bin_stock_list[j].pick_qty - \
                                               goods_bin_stock_list[j].picked_qty
                            if bin_can_pick_qty > 0:
                                dn_need_pick_qty = dn_detail_list[i].goods_qty - \
                                                   dn_detail_list[i].pick_qty - \
                                                   dn_detail_list[i].picked_qty
                                if dn_need_pick_qty > bin_can_pick_qty:
                                    goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[j].pick_qty + \
                                                                       bin_can_pick_qty
                                    goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - \
                                                                     bin_can_pick_qty
                                    goods_qty_change.pick_stock = goods_qty_change.pick_stock + \
                                                                  bin_can_pick_qty
                                    picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                         dn_code=dn_detail_list[i].dn_code,
                                                                         bin_name=goods_bin_stock_list[j].bin_name,
                                                                         goods_code=goods_bin_stock_list[
                                                                             i].goods_code,
                                                                         pick_qty=bin_can_pick_qty,
                                                                         creater=self.request.auth.name))
                                    picking_list_label = 1
                                    dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + \
                                                                 bin_can_pick_qty
                                    dn_detail_list[i].save()
                                    goods_bin_stock_list[j].save()
                                    goods_qty_change.save()
                                elif dn_need_pick_qty == bin_can_pick_qty:
                                    goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                           j].pick_qty + bin_can_pick_qty
                                    goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                    goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                    picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                         dn_code=dn_detail_list[i].dn_code,
                                                                         bin_name=goods_bin_stock_list[j].bin_name,
                                                                         goods_code=goods_bin_stock_list[
                                                                             i].goods_code,
                                                                         pick_qty=bin_can_pick_qty,
                                                                         creater=self.request.auth.name))
                                    picking_list_label = 1
                                    dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + bin_can_pick_qty
                                    dn_detail_list[i].dn_status = 3
                                    dn_detail_list[i].save()
                                    goods_bin_stock_list[j].save()
                                    goods_qty_change.save()
                                    break
                                elif dn_need_pick_qty < bin_can_pick_qty:
                                    goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[j].pick_qty + \
                                                                       dn_need_pick_qty
                                    goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - \
                                                                     dn_need_pick_qty
                                    goods_qty_change.pick_stock = goods_qty_change.pick_stock + \
                                                                  dn_need_pick_qty
                                    picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                         dn_code=dn_detail_list[i].dn_code,
                                                                         bin_name=goods_bin_stock_list[j].bin_name,
                                                                         goods_code=goods_bin_stock_list[
                                                                             i].goods_code,
                                                                         pick_qty=dn_need_pick_qty,
                                                                         creater=self.request.auth.name))
                                    picking_list_label = 1
                                    dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + dn_need_pick_qty
                                    dn_detail_list[i].dn_status = 3
                                    dn_detail_list[i].save()
                                    goods_bin_stock_list[j].save()
                                    goods_qty_change.save()
                                    break
                                else:
                                    break
                            elif bin_can_pick_qty == 0:
                                continue
                            else:
                                continue
                    else:
                        continue
                elif can_pick_qty == 0:
                    if qs[v].back_order_label == False:
                        goods_qty_change.back_order_stock = goods_qty_change.back_order_stock + dn_detail_list[
                            i].goods_qty
                        back_order_goods_volume = round(goods_detail.unit_volume * dn_detail_list[i].goods_qty, 4)
                        back_order_goods_weight = round(
                            (goods_detail.goods_weight * dn_detail_list[i].goods_qty) / 1000, 4)
                        back_order_list.append(DnDetailModel(dn_code=back_order_dn_code,
                                                             dn_status=2,
                                                             customer=qs[v].customer,
                                                             goods_code=dn_detail_list[i].goods_code,
                                                             goods_qty=dn_detail_list[i].goods_qty,
                                                             goods_weight=back_order_goods_weight,
                                                             goods_volume=back_order_goods_volume,
                                                             creater=self.request.auth.name,
                                                             back_order_label=True,
                                                             openid=self.request.auth.openid,
                                                             create_time=dn_detail_list[i].create_time))
                        back_order_list_label = 1
                        total_weight = total_weight - back_order_goods_weight
                        total_volume = total_volume - back_order_goods_volume
                        back_order_goods_weight_list.append(back_order_goods_weight)
                        back_order_goods_volume_list.append(back_order_goods_volume)
                        dn_detail_list[i].is_delete = True
                        dn_detail_list[i].save()
                        goods_qty_change.save()
                    else:
                        continue
                else:
                    continue
            if picking_list_label == 1:
                if back_order_list_label == 1:
                    back_order_total_volume = sumOfList(back_order_goods_volume_list,
                                                        len(back_order_goods_volume_list))
                    back_order_total_weight = sumOfList(back_order_goods_weight_list,
                                                        len(back_order_goods_weight_list))
                    customer_city = customer.objects.filter(openid=self.request.auth.openid,
                                                            customer_name=str(qs[v].customer),
                                                            is_delete=False).first().customer_city
                    warehouse_city = warehouse.objects.filter(
                        openid=self.request.auth.openid).first().warehouse_city
                    transportation_fee = transportation.objects.filter(
                        Q(openid=self.request.auth.openid, send_city__icontains=warehouse_city,
                          receiver_city__icontains=customer_city,
                          is_delete=False) | Q(openid='init_data', send_city__icontains=warehouse_city,
                                               receiver_city__icontains=customer_city,
                                               is_delete=False))
                    transportation_res = {
                        "detail": []
                    }
                    transportation_back_order_res = {
                        "detail": []
                    }
                    if len(transportation_fee) >= 1:
                        transportation_list = []
                        transportation_back_order_list = []
                        for k in range(len(transportation_fee)):
                            transportation_cost = transportation_calculate(total_weight,
                                                                           total_volume,
                                                                           transportation_fee[k].weight_fee,
                                                                           transportation_fee[k].volume_fee,
                                                                           transportation_fee[k].min_payment)
                            transportation_back_order_cost = transportation_calculate(back_order_total_weight,
                                                                                      back_order_total_volume,
                                                                                      transportation_fee[
                                                                                          k].weight_fee,
                                                                                      transportation_fee[
                                                                                          k].volume_fee,
                                                                                      transportation_fee[
                                                                                          k].min_payment)
                            transportation_detail = {
                                "transportation_supplier": transportation_fee[k].transportation_supplier,
                                "transportation_cost": transportation_cost
                            }
                            transportation_back_order_detail = {
                                "transportation_supplier": transportation_fee[k].transportation_supplier,
                                "transportation_cost": transportation_back_order_cost
                            }
                            transportation_list.append(transportation_detail)
                            transportation_back_order_list.append(transportation_back_order_detail)
                        transportation_res['detail'] = transportation_list
                        transportation_back_order_res['detail'] = transportation_back_order_list
                    DnListModel.objects.create(openid=self.request.auth.openid,
                                               dn_code=back_order_dn_code,
                                               dn_status=2,
                                               total_weight=back_order_total_weight,
                                               total_volume=back_order_total_volume,
                                               customer=qs[v].customer,
                                               creater=self.request.auth.name,
                                               back_order_label=True,
                                               transportation_fee=transportation_back_order_res,
                                               create_time=qs[v].create_time)
                    PickingListModel.objects.bulk_create(picking_list, batch_size=100)
                    DnDetailModel.objects.bulk_create(back_order_list, batch_size=100)
                    qs[v].total_weight = total_weight
                    qs[v].total_volume = total_volume
                    qs[v].transportation_fee = transportation_res
                    qs[v].dn_status = 3
                    qs[v].save()
                elif back_order_list_label == 0:
                    PickingListModel.objects.bulk_create(picking_list, batch_size=100)
                    qs[v].dn_status = 3
                    qs[v].save()
                else:
                    continue
            elif picking_list_label == 0:
                if back_order_list_label == 1:
                    DnDetailModel.objects.bulk_create(back_order_list, batch_size=100)
                    DnListModel.objects.create(openid=self.request.auth.openid,
                                               dn_code=back_order_dn_code,
                                               dn_status=2,
                                               total_weight=qs[v].total_weight,
                                               total_volume=qs[v].total_volume,
                                               customer=qs[v].customer,
                                               creater=self.request.auth.name,
                                               back_order_label=True,
                                               transportation_fee=qs[v].transportation_fee,
                                               create_time=qs[v].create_time)
                    qs[v].is_delete = True
                    qs[v].dn_status = 3
                    qs[v].save()
                elif back_order_list_label == 0:
                    continue
                else:
                    continue
            else:
                continue
        return Response({"detail": "success"}, status=200)

    def update(self, request, pk):
        qs = self.get_object()
        if qs.openid != self.request.auth.openid:
            raise APIException({"detail": "Cannot Release Order Data Which Not Yours"})
        else:
            if qs.dn_status == 2:
                dn_detail_list = DnDetailModel.objects.filter(openid=self.request.auth.openid, dn_code=qs.dn_code,
                                                                dn_status=2, is_delete=False)
                picking_list = []
                picking_list_label = 0
                back_order_list = []
                back_order_list_label = 0
                back_order_goods_weight_list = []
                back_order_goods_volume_list = []
                back_order_base_code = DnListModel.objects.filter(openid=self.request.auth.openid, is_delete=False).order_by('-id').first().dn_code
                dn_last_code = re.findall(r'\d+', str(back_order_base_code), re.IGNORECASE)
                back_order_dn_code = 'DN' + str(int(dn_last_code[0]) + 1).zfill(8)
                total_weight = qs.total_weight
                total_volume = qs.total_volume
                for i in range(len(dn_detail_list)):
                    goods_detail = goods.objects.filter(openid=self.request.auth.openid,
                                                        goods_code=str(dn_detail_list[i].goods_code),
                                                        is_delete=False).first()
                    if stocklist.objects.filter(openid=self.request.auth.openid,
                                                goods_code=str(dn_detail_list[i].goods_code)).exists():
                        pass
                    else:
                        stocklist.objects.create(openid=self.request.auth.openid,
                                                 goods_code=str(goods_detail.goods_code),
                                                 goods_desc=goods_detail.goods_desc,
                                                 dn_stock=int(dn_detail_list[i].goods_qty))
                    goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                goods_code=str(
                                                                    dn_detail_list[i].goods_code)).first()
                    goods_bin_stock_list = stockbin.objects.filter(openid=self.request.auth.openid,
                                                                   goods_code=str(dn_detail_list[i].goods_code),
                                                                   bin_property="Normal").order_by('-id')
                    can_pick_qty = goods_qty_change.onhand_stock - \
                                   goods_qty_change.inspect_stock - \
                                   goods_qty_change.hold_stock - \
                                   goods_qty_change.damage_stock - \
                                   goods_qty_change.pick_stock - \
                                   goods_qty_change.picked_stock
                    if can_pick_qty > 0:
                        if dn_detail_list[i].goods_qty > can_pick_qty:
                            if qs.back_order_label == False:
                                dn_pick_qty = dn_detail_list[i].pick_qty
                                for j in range(len(goods_bin_stock_list)):
                                    bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - \
                                                       goods_bin_stock_list[j].pick_qty - \
                                                       goods_bin_stock_list[j].picked_qty
                                    if bin_can_pick_qty > 0:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                               j].pick_qty + bin_can_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[
                                                                                 i].goods_code,
                                                                             pick_qty=bin_can_pick_qty,
                                                                             creater=self.request.auth.name))
                                        picking_list_label = 1
                                        dn_pick_qty = dn_pick_qty + bin_can_pick_qty
                                        goods_qty_change.save()
                                        goods_bin_stock_list[j].save()
                                    elif bin_can_pick_qty == 0:
                                        continue
                                    else:
                                        continue
                                dn_detail_list[i].pick_qty = dn_pick_qty
                                dn_back_order_qty = dn_detail_list[i].goods_qty - \
                                                   dn_detail_list[i].pick_qty - \
                                                   dn_detail_list[i].picked_qty
                                dn_detail_list[i].goods_qty = dn_pick_qty
                                dn_detail_list[i].dn_status = 3
                                goods_qty_change.back_order_stock = goods_qty_change.back_order_stock + \
                                                                    dn_back_order_qty
                                back_order_goods_volume = round(goods_detail.unit_volume * dn_back_order_qty, 4)
                                back_order_goods_weight = round(
                                    (goods_detail.goods_weight * dn_back_order_qty) / 1000, 4)
                                back_order_list.append(DnDetailModel(dn_code=back_order_dn_code,
                                                                     dn_status=2,
                                                                     customer=qs.customer,
                                                                     goods_code=dn_detail_list[i].goods_code,
                                                                     goods_qty=dn_back_order_qty,
                                                                     goods_weight=back_order_goods_weight,
                                                                     goods_volume=back_order_goods_volume,
                                                                     creater=self.request.auth.name,
                                                                     back_order_label=True,
                                                                     openid=self.request.auth.openid,
                                                                     create_time=dn_detail_list[i].create_time))
                                back_order_list_label = 1
                                total_weight = total_weight - back_order_goods_weight
                                total_volume = total_volume - back_order_goods_volume
                                dn_detail_list[i].goods_weight = dn_detail_list[i].goods_weight - \
                                                                 back_order_goods_weight
                                dn_detail_list[i].goods_volume = dn_detail_list[i].goods_volume - \
                                                                 back_order_goods_volume
                                back_order_goods_weight_list.append(back_order_goods_weight)
                                back_order_goods_volume_list.append(back_order_goods_volume)
                                goods_qty_change.save()
                                dn_detail_list[i].save()
                            else:
                                dn_pick_qty = dn_detail_list[i].pick_qty
                                for j in range(len(goods_bin_stock_list)):
                                    bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - \
                                                       goods_bin_stock_list[j].pick_qty - \
                                                       goods_bin_stock_list[j].picked_qty
                                    if bin_can_pick_qty > 0:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                               j].pick_qty + bin_can_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[
                                                                                 i].goods_code,
                                                                             pick_qty=bin_can_pick_qty,
                                                                             creater=self.request.auth.name))
                                        picking_list_label = 1
                                        dn_pick_qty = dn_pick_qty + bin_can_pick_qty
                                        goods_qty_change.save()
                                        goods_bin_stock_list[j].save()
                                    elif bin_can_pick_qty == 0:
                                        continue
                                    else:
                                        continue
                                dn_detail_list[i].pick_qty = dn_pick_qty
                                dn_back_order_qty = dn_detail_list[i].goods_qty - \
                                                    dn_detail_list[i].pick_qty - \
                                                    dn_detail_list[i].picked_qty
                                dn_detail_list[i].goods_qty = dn_pick_qty
                                dn_detail_list[i].dn_status = 3
                                back_order_goods_volume = round(goods_detail.unit_volume * dn_back_order_qty, 4)
                                back_order_goods_weight = round(
                                    (goods_detail.goods_weight * dn_back_order_qty) / 1000, 4)
                                back_order_list.append(DnDetailModel(dn_code=back_order_dn_code,
                                                                     dn_status=2,
                                                                     customer=qs.customer,
                                                                     goods_code=dn_detail_list[i].goods_code,
                                                                     goods_qty=dn_back_order_qty,
                                                                     goods_weight=back_order_goods_weight,
                                                                     goods_volume=back_order_goods_volume,
                                                                     creater=self.request.auth.name,
                                                                     back_order_label=True,
                                                                     openid=self.request.auth.openid,
                                                                     create_time=dn_detail_list[i].create_time))
                                back_order_list_label = 1
                                total_weight = total_weight - back_order_goods_weight
                                total_volume = total_volume - back_order_goods_volume
                                dn_detail_list[i].goods_weight = dn_detail_list[i].goods_weight - \
                                                                 back_order_goods_weight
                                dn_detail_list[i].goods_volume = dn_detail_list[i].goods_volume - \
                                                                 back_order_goods_volume
                                back_order_goods_weight_list.append(back_order_goods_weight)
                                back_order_goods_volume_list.append(back_order_goods_volume)
                                dn_detail_list[i].save()
                        elif dn_detail_list[i].goods_qty == can_pick_qty:
                            for j in range(len(goods_bin_stock_list)):
                                bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - goods_bin_stock_list[j].pick_qty - \
                                                   goods_bin_stock_list[j].picked_qty
                                if bin_can_pick_qty > 0:
                                    dn_need_pick_qty = dn_detail_list[i].goods_qty - dn_detail_list[i].pick_qty - dn_detail_list[i].picked_qty
                                    if dn_need_pick_qty > bin_can_pick_qty:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                               j].pick_qty + bin_can_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[j].goods_code,
                                                                             pick_qty=bin_can_pick_qty,
                                                                             creater=self.request.auth.name))
                                        picking_list_label = 1
                                        dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + bin_can_pick_qty
                                        goods_bin_stock_list[j].save()
                                        goods_qty_change.save()
                                    elif dn_need_pick_qty == bin_can_pick_qty:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                               j].pick_qty + bin_can_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[j].goods_code,
                                                                             pick_qty=bin_can_pick_qty,
                                                                             creater=self.request.auth.name))
                                        picking_list_label = 1
                                        dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + bin_can_pick_qty
                                        dn_detail_list[i].dn_status = 3
                                        dn_detail_list[i].save()
                                        goods_bin_stock_list[j].save()
                                        goods_qty_change.save()
                                        break
                                    else:
                                        break
                                elif bin_can_pick_qty == 0:
                                    continue
                                else:
                                    continue
                        elif dn_detail_list[i].goods_qty < can_pick_qty:
                            for j in range(len(goods_bin_stock_list)):
                                bin_can_pick_qty = goods_bin_stock_list[j].goods_qty - \
                                                   goods_bin_stock_list[j].pick_qty - \
                                                   goods_bin_stock_list[j].picked_qty
                                if bin_can_pick_qty > 0:
                                    dn_need_pick_qty = dn_detail_list[i].goods_qty - \
                                                       dn_detail_list[i].pick_qty - \
                                                       dn_detail_list[i].picked_qty
                                    if dn_need_pick_qty > bin_can_pick_qty:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[j].pick_qty + \
                                                                           bin_can_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - \
                                                                         bin_can_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + \
                                                                      bin_can_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[j].goods_code,
                                                                             pick_qty=bin_can_pick_qty,
                                                                             creater=self.request.auth.name))
                                        picking_list_label = 1
                                        dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + \
                                                                     bin_can_pick_qty
                                        dn_detail_list[i].save()
                                        goods_bin_stock_list[j].save()
                                        goods_qty_change.save()
                                    elif dn_need_pick_qty == bin_can_pick_qty:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[
                                                                               j].pick_qty + bin_can_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - bin_can_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + bin_can_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[j].goods_code,
                                                                             pick_qty=bin_can_pick_qty,
                                                                             creater=self.request.auth.name))
                                        picking_list_label = 1
                                        dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + bin_can_pick_qty
                                        dn_detail_list[i].dn_status = 3
                                        dn_detail_list[i].save()
                                        goods_bin_stock_list[j].save()
                                        goods_qty_change.save()
                                        break
                                    elif dn_need_pick_qty < bin_can_pick_qty:
                                        goods_bin_stock_list[j].pick_qty = goods_bin_stock_list[j].pick_qty + \
                                                                           dn_need_pick_qty
                                        goods_qty_change.ordered_stock = goods_qty_change.ordered_stock - \
                                                                         dn_need_pick_qty
                                        goods_qty_change.pick_stock = goods_qty_change.pick_stock + \
                                                                      dn_need_pick_qty
                                        picking_list.append(PickingListModel(openid=self.request.auth.openid,
                                                                             dn_code=dn_detail_list[i].dn_code,
                                                                             bin_name=goods_bin_stock_list[j].bin_name,
                                                                             goods_code=goods_bin_stock_list[j].goods_code,
                                                                             pick_qty=dn_need_pick_qty,
                                                                             creater=self.request.auth.name))
                                        picking_list_label = 1
                                        dn_detail_list[i].pick_qty = dn_detail_list[i].pick_qty + dn_need_pick_qty
                                        dn_detail_list[i].dn_status = 3
                                        dn_detail_list[i].save()
                                        goods_bin_stock_list[j].save()
                                        goods_qty_change.save()
                                        break
                                    else:
                                        break
                                elif bin_can_pick_qty == 0:
                                    continue
                                else:
                                    continue
                        else:
                            pass
                    elif can_pick_qty == 0:
                        if qs.back_order_label == False:
                            goods_qty_change.back_order_stock = goods_qty_change.back_order_stock + dn_detail_list[i].goods_qty
                            back_order_goods_volume = round(goods_detail.unit_volume * dn_detail_list[i].goods_qty, 4)
                            back_order_goods_weight = round((goods_detail.goods_weight * dn_detail_list[i].goods_qty) / 1000, 4)
                            back_order_list.append(DnDetailModel(dn_code=back_order_dn_code,
                                                                 dn_status=2,
                                                                 customer=qs.customer,
                                                                 goods_code=dn_detail_list[i].goods_code,
                                                                 goods_qty=dn_detail_list[i].goods_qty,
                                                                 goods_weight=back_order_goods_weight,
                                                                 goods_volume=back_order_goods_volume,
                                                                 creater=self.request.auth.name,
                                                                 back_order_label=True,
                                                                 openid=self.request.auth.openid,
                                                                 create_time=dn_detail_list[i].create_time))
                            back_order_list_label = 1
                            total_weight = total_weight - back_order_goods_weight
                            total_volume = total_volume - back_order_goods_volume
                            back_order_goods_weight_list.append(back_order_goods_weight)
                            back_order_goods_volume_list.append(back_order_goods_volume)
                            dn_detail_list[i].is_delete = True
                            dn_detail_list[i].save()
                            goods_qty_change.save()
                        else:
                            continue
                    else:
                        continue
                if picking_list_label == 1:
                    if back_order_list_label == 1:
                        back_order_total_volume = sumOfList(back_order_goods_volume_list,
                                                            len(back_order_goods_volume_list))
                        back_order_total_weight = sumOfList(back_order_goods_weight_list,
                                                            len(back_order_goods_weight_list))
                        customer_city = customer.objects.filter(openid=self.request.auth.openid,
                                                                customer_name=str(qs.customer),
                                                                is_delete=False).first().customer_city
                        warehouse_city = warehouse.objects.filter(
                            openid=self.request.auth.openid).first().warehouse_city
                        transportation_fee = transportation.objects.filter(
                            Q(openid=self.request.auth.openid, send_city__icontains=warehouse_city,
                              receiver_city__icontains=customer_city,
                              is_delete=False) | Q(openid='init_data', send_city__icontains=warehouse_city,
                                                   receiver_city__icontains=customer_city,
                                                   is_delete=False))
                        transportation_res = {
                            "detail": []
                        }
                        transportation_back_order_res = {
                            "detail": []
                        }
                        if len(transportation_fee) >= 1:
                            transportation_list = []
                            transportation_back_order_list = []
                            for k in range(len(transportation_fee)):
                                transportation_cost = transportation_calculate(total_weight,
                                                                               total_volume,
                                                                               transportation_fee[k].weight_fee,
                                                                               transportation_fee[k].volume_fee,
                                                                               transportation_fee[k].min_payment)
                                transportation_back_order_cost = transportation_calculate(back_order_total_weight,
                                                                               back_order_total_volume,
                                                                               transportation_fee[k].weight_fee,
                                                                               transportation_fee[k].volume_fee,
                                                                               transportation_fee[k].min_payment)
                                transportation_detail = {
                                    "transportation_supplier": transportation_fee[k].transportation_supplier,
                                    "transportation_cost": transportation_cost
                                }
                                transportation_back_order_detail = {
                                    "transportation_supplier": transportation_fee[k].transportation_supplier,
                                    "transportation_cost": transportation_back_order_cost
                                }
                                transportation_list.append(transportation_detail)
                                transportation_back_order_list.append(transportation_back_order_detail)
                            transportation_res['detail'] = transportation_list
                            transportation_back_order_res['detail'] = transportation_back_order_list
                        DnListModel.objects.create(openid=self.request.auth.openid,
                                                   dn_code=back_order_dn_code,
                                                   dn_status=2,
                                                   total_weight=back_order_total_weight,
                                                   total_volume=back_order_total_volume,
                                                   customer=qs.customer,
                                                   creater=self.request.auth.name,
                                                   back_order_label=True,
                                                   transportation_fee=transportation_back_order_res,
                                                   create_time=qs.create_time)
                        PickingListModel.objects.bulk_create(picking_list, batch_size=100)
                        DnDetailModel.objects.bulk_create(back_order_list, batch_size=100)
                        qs.total_weight = total_weight
                        qs.total_volume = total_volume
                        qs.transportation_fee = transportation_res
                        qs.dn_status = 3
                        qs.save()
                    elif back_order_list_label == 0:
                        PickingListModel.objects.bulk_create(picking_list, batch_size=100)
                        qs.dn_status = 3
                        qs.save()
                        return Response({"detail": "success"}, status=200)
                    else:
                        raise APIException({"detail": "This Order Does Not in Release Status"})
                elif picking_list_label == 0:
                    if back_order_list_label == 1:
                        DnDetailModel.objects.bulk_create(back_order_list, batch_size=100)
                        DnListModel.objects.create(openid=self.request.auth.openid,
                                                   dn_code=back_order_dn_code,
                                                   dn_status=2,
                                                   total_weight=qs.total_weight,
                                                   total_volume=qs.total_volume,
                                                   customer=qs.customer,
                                                   creater=self.request.auth.name,
                                                   back_order_label=True,
                                                   transportation_fee=qs.transportation_fee,
                                                   create_time=qs.create_time)
                        qs.is_delete = True
                        qs.dn_status = 3
                        qs.save()
                    elif back_order_list_label == 0:
                        return Response({"detail": "success"}, status=200)
                    else:
                        raise APIException({"detail": "This Order Does Not in Release Status"})
                else:
                    raise APIException({"detail": "This Order Does Not in Release Status"})
                return Response({"detail": "success"}, status=200)
            else:
                raise APIException({"detail": "This Order Does Not in Release Status"})

class DnPickingListViewSet(viewsets.ModelViewSet):
    """
        retrieve:
            Picklist for pk
    """
    queryset = DnListModel.objects.all()
    serializer_class = serializers.DNListGetSerializer
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            return self.queryset.filter(openid=self.request.auth.openid, id=id)
        else:
            return self.queryset.none()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.DNListGetSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def retrieve(self, request, pk):
        qs = self.get_object()
        if qs.dn_status != 3:
            raise APIException({"detail": "This DN Status Not 3"})
        else:
            picking_qs = PickingListModel.objects.filter(openid=self.request.auth.openid, dn_code=qs.dn_code)
            serializer = serializers.DNPickingListGetSerializer(picking_qs, many=True)
            return Response(serializer.data, status=200)

class DnPickingListFilterViewSet(viewsets.ModelViewSet):
    """
        list:
            Picklist for Filter
    """
    queryset = DnListModel.objects.all()
    serializer_class = serializers.DNListGetSerializer
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            return self.queryset.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return self.queryset.none()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.DNListGetSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, pk):
        qs = self.get_object()
        if qs.dn_status != 4:
            raise APIException({"detail": "This DN Status Not 4"})
        else:
            qs.dn_status = 5
            print(qs.dn_code)
            return Response({"ok": "ok"}, status=200)

class DnPickedViewSet(viewsets.ModelViewSet):
    """
        create:
            Finish Picked
    """
    queryset = DnListModel.objects.all()
    serializer_class = serializers.DNListPostSerializer
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            if id is None:
                return self.queryset.filter(openid=self.request.auth.openid, is_delete=False)
            else:
                return self.queryset.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return self.queryset.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.DNListPostSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, pk):
        qs = self.get_object()
        if qs.dn_status != 3:
            raise APIException({"detail": "This dn Status does not correct"})
        else:
            data = request.data
            for i in range(len(data['goodsData'])):
                pick_qty_change = PickingListModel.objects.filter(openid=self.request.auth.openid,
                                                                  dn_code=str(data['dn_code']),
                                                                  goods_code=str(data['goodsData'][i].get('goods_code')),
                                                                  bin_name=str(data['goodsData'][i].get('bin_name'))).first()
                if int(data['goodsData'][i].get('pick_qty')) > pick_qty_change.pick_qty:
                    raise APIException({"detail": str(data['goodsData'][i].get('goods_code')) + "Picked Qty Must Less Than Pick Qty"})
                else:
                    continue
            qs.dn_status = 4
            for j in range(len(data['goodsData'])):
                goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                            goods_code=str(data['goodsData'][j].get('goods_code'))).first()
                dn_detail = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                                         dn_code=str(data['dn_code']),
                                                         dn_status=3, customer=str(data['customer']),
                                                         goods_code=str(data['goodsData'][j].get('goods_code'))).first()
                bin_qty_change = stockbin.objects.filter(openid=self.request.auth.openid,
                                                         goods_code=str(data['goodsData'][j].get('goods_code')),
                                                         bin_name=str(data['goodsData'][j].get('bin_name'))).first()
                pick_qty_change = PickingListModel.objects.filter(openid=self.request.auth.openid,
                                                                  dn_code=str(data['dn_code']),
                                                                  goods_code=str(data['goodsData'][j].get('goods_code')),
                                                                  bin_name=str(data['goodsData'][j].get('bin_name'))).first()
                if int(data['goodsData'][j].get('pick_qty')) == pick_qty_change.pick_qty:
                    goods_qty_change.pick_stock = goods_qty_change.pick_stock - int(data['goodsData'][j].get('pick_qty'))
                    goods_qty_change.picked_stock = goods_qty_change.picked_stock + int(data['goodsData'][j].get('pick_qty'))
                    pick_qty_change.picked_qty = int(data['goodsData'][j].get('pick_qty'))
                    bin_qty_change.pick_qty = bin_qty_change.pick_qty - int(data['goodsData'][j].get('pick_qty'))
                    bin_qty_change.picked_qty = bin_qty_change.picked_qty + int(data['goodsData'][j].get('pick_qty'))
                    goods_qty_change.save()
                    pick_qty_change.save()
                    bin_qty_change.save()
                elif int(data['goodsData'][j].get('pick_qty')) < pick_qty_change.pick_qty:
                    goods_qty_change.pick_stock = goods_qty_change.pick_stock - dn_detail.pick_qty
                    goods_qty_change.picked_stock = goods_qty_change.picked_stock + int(data['goodsData'][j].get('pick_qty'))
                    pick_qty_change.picked_qty = int(data['goodsData'][j].get('pick_qty'))
                    bin_qty_change.pick_qty = bin_qty_change.pick_qty - pick_qty_change.pick_stock
                    bin_qty_change.picked_qty = bin_qty_change.picked_qty + int(data['goodsData'][j].get('pick_qty'))
                    goods_qty_change.save()
                    pick_qty_change.save()
                    bin_qty_change.save()
                else:
                    continue
                dn_detail.picked_qty = dn_detail.picked_qty + int(data['goodsData'][j].get('pick_qty'))
                if dn_detail.dn_status == 3:
                    dn_detail.dn_status = 4
                else:
                    pass
                if dn_detail.pick_qty > 0:
                    dn_detail.pick_qty = 0
                else:
                    pass
                dn_detail.save()
            qs.save()
            return Response({"Detail": "Success Confirm Picking List"}, status=200)

class DnDispatchViewSet(viewsets.ModelViewSet):
    """
        create:
            Confirm Dispatch
    """
    queryset = DnListModel.objects.all()
    serializer_class = serializers.DNListPostSerializer
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            return self.queryset.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return self.queryset.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.DNListPostSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, pk):
        qs = self.get_object()
        if qs.dn_status != 4:
            raise APIException({"detail": "This DN Status Not 4"})
        else:
            qs.dn_status = 5
            data = self.request.data
            if driverlist.objects.filter(openid=self.request.auth.openid,
                                               is_delete=False).exists():
                driver = driverlist.objects.filter(openid=self.request.auth.openid,
                                                   driver_name=str(data['driver']),
                                                   is_delete=False).first()
                dn_detail = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                                         dn_code=str(data['dn_code']),
                                                         dn_status=4, customer=qs.customer,
                                                         )
                pick_qty_change = PickingListModel.objects.filter(openid=self.request.auth.openid,
                                                                  dn_code=str(data['dn_code']))
                for i in range(len(dn_detail)):
                    goods_qty_change = stocklist.objects.filter(openid=self.request.auth.openid,
                                                                goods_code=dn_detail[i].goods_code).first()
                    goods_qty_change.goods_qty = goods_qty_change.goods_qty - dn_detail[i].picked_qty
                    goods_qty_change.onhand_stock = goods_qty_change.onhand_stock - dn_detail[i].picked_qty
                    goods_qty_change.picked_stock = goods_qty_change.picked_stock - dn_detail[i].picked_qty
                    dn_detail[i].dn_status = 5
                    dn_detail[i].intransit_qty = dn_detail[i].picked_qty
                    dn_detail[i].picked_qty = 0
                    dn_detail[i].save()
                    goods_qty_change.save()
                for j in range(len(pick_qty_change)):
                    bin_qty_change = stockbin.objects.filter(openid=self.request.auth.openid,
                                                             goods_code=pick_qty_change[j].goods_code,
                                                             bin_name=pick_qty_change[j].bin_name).first()
                    bin_qty_change.goods_qty = bin_qty_change.goods_qty - pick_qty_change[j].picked_qty
                    bin_qty_change.picked_qty = bin_qty_change.picked_qty - pick_qty_change[j].picked_qty
                    bin_qty_change.save()
                driverdispatch.objects.create(openid=self.request.auth.openid,
                                              driver_name=driver.driver_name,
                                              dn_code=str(data['dn_code']),
                                              contact=driver.contact,
                                              creater=self.request.auth.name)
                qs.save()
                return Response({"detail": "Success Dispatch DN"}, status=200)
            else:
                raise APIException({"detail": "Driver Does Not Exists"})

class DnPODViewSet(viewsets.ModelViewSet):
    """
        create:
            Confirm Dispatch
    """
    queryset = DnListModel.objects.all()
    serializer_class = serializers.DNListPostSerializer
    pagination_class = MyPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            return self.queryset.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return self.queryset.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.DNListPostSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def create(self, request, pk):
        qs = self.get_object()
        if qs.dn_status != 5:
            raise APIException({"detail": "This DN Status Not 5"})
        else:
            qs.dn_status = 6
            data = self.request.data
            for i in range(len(data['goodsData'])):
                delivery_damage_qty = data['goodsData'][i].get('delivery_damage_qty')
                if delivery_damage_qty < 0:
                    raise APIException({"detail": "Delivery Damage QTY Must Greater Than 0"})
            dn_detail = DnDetailModel.objects.filter(openid=self.request.auth.openid,
                                                     dn_code=str(data['dn_code']),
                                                     dn_status=5, customer=qs.customer,
                                                     )
            for j in range(len(data['goodsData'])):
                delivery_damage_qty = data['goodsData'][j].get('delivery_damage_qty')
                delivery_actual_qty = data['goodsData'][j].get('intransit_qty')
                goods_code = data['goodsData'][j].get('goods_code')
                if delivery_damage_qty > 0:
                    goods_detail = dn_detail.filter(goods_code=goods_code).first()
                    if delivery_actual_qty > goods_detail.intransit_qty:
                        goods_detail.delivery_actual_qty = delivery_actual_qty
                        goods_detail.delivery_more_qty = delivery_actual_qty - goods_detail.intransit_qty
                        goods_detail.delivery_damage_qty = delivery_damage_qty
                        goods_detail.intransit_qty = 0
                        goods_detail.dn_status = 6
                    elif delivery_actual_qty < goods_detail.intransit_qty:
                        goods_detail.delivery_actual_qty = delivery_actual_qty
                        goods_detail.delivery_shortage_qty = goods_detail.intransit_qty - delivery_actual_qty
                        goods_detail.delivery_damage_qty = delivery_damage_qty
                        goods_detail.intransit_qty = 0
                        goods_detail.dn_status = 6
                    elif delivery_actual_qty == goods_detail.intransit_qty:
                        goods_detail.delivery_actual_qty = delivery_actual_qty
                        goods_detail.delivery_damage_qty = delivery_damage_qty
                        goods_detail.intransit_qty = 0
                        goods_detail.dn_status = 6
                    else:
                        continue
                    goods_detail.save()
                elif delivery_damage_qty == 0:
                    goods_detail = dn_detail.filter(goods_code=goods_code).first()
                    if delivery_actual_qty > goods_detail.intransit_qty:
                        goods_detail.delivery_actual_qty = delivery_actual_qty
                        goods_detail.delivery_more_qty = delivery_actual_qty - goods_detail.intransit_qty
                        goods_detail.intransit_qty = 0
                        goods_detail.dn_status = 6
                    elif delivery_actual_qty < goods_detail.intransit_qty:
                        goods_detail.delivery_actual_qty = delivery_actual_qty
                        goods_detail.delivery_shortage_qty = goods_detail.intransit_qty - delivery_actual_qty
                        goods_detail.intransit_qty = 0
                        goods_detail.dn_status = 6
                    elif delivery_actual_qty == goods_detail.intransit_qty:
                        goods_detail.delivery_actual_qty = delivery_actual_qty
                        goods_detail.intransit_qty = 0
                        goods_detail.dn_status = 6
                    else:
                        continue
                    goods_detail.save()
            qs.save()
            return Response({"detail": "Success Delivery DN"}, status=200)


class FileListDownloadView(viewsets.ModelViewSet):
    queryset = DnListModel.objects.all()
    serializer_class = serializers.FileListRenderSerializer
    renderer_classes = (FileListRenderCN, ) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnListFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            if id is None:
                return self.queryset.filter(openid=self.request.auth.openid, is_delete=False)
            else:
                return self.queryset.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return self.queryset.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.FileListRenderSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def list(self, request, *args, **kwargs):
        from datetime import datetime
        dt = datetime.now()
        data = (
            FileListRenderSerializer(instance).data
            for instance in self.get_queryset()
        )
        if self.request.GET.get('lang', '') == 'zh-hans':
            renderer = FileListRenderCN().render(data)
        else:
            renderer = FileListRenderEN().render(data)
        response = StreamingHttpResponse(
            renderer,
            content_type="text/csv"
        )
        response['Content-Disposition'] = "attachment; filename='dnlist_{}.csv'".format(str(dt.strftime('%Y%m%d%H%M%S%f')))
        return response

class FileDetailDownloadView(viewsets.ModelViewSet):
    queryset = DnDetailModel.objects.all()
    serializer_class = serializers.FileDetailRenderSerializer
    renderer_classes = (FileDetailRenderCN, ) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering_fields = ['id', "create_time", "update_time", ]
    filter_class = DnDetailFilter

    def get_project(self):
        try:
            id = self.kwargs.get('pk')
            return id
        except:
            return None

    def get_queryset(self):
        id = self.get_project()
        if self.request.user:
            if id is None:
                return self.queryset.filter(openid=self.request.auth.openid, is_delete=False)
            else:
                return self.queryset.filter(openid=self.request.auth.openid, id=id, is_delete=False)
        else:
            return self.queryset.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.FileDetailRenderSerializer
        else:
            return self.http_method_not_allowed(request=self.request)

    def list(self, request, *args, **kwargs):
        from datetime import datetime
        dt = datetime.now()
        data = (
            FileDetailRenderSerializer(instance).data
            for instance in self.get_queryset()
        )
        if self.request.GET.get('lang', '') == 'zh-hans':
            renderer = FileDetailRenderCN().render(data)
        else:
            renderer = FileDetailRenderEN().render(data)
        response = StreamingHttpResponse(
            renderer,
            content_type="text/csv"
        )
        response['Content-Disposition'] = "attachment; filename='dndetail_{}.csv'".format(str(dt.strftime('%Y%m%d%H%M%S%f')))
        return response
