
# django methods
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.urls import reverse

# PostgreSQL
import psycopg2

# ORMs
from bmstu_lab_m.models import Cargo
from bmstu_lab_m.models import CargoOrder
from bmstu_lab_m.models import DeliveryOrders
#from bmstu_lab_m.models import DeliveryOrders
from bmstu_lab_m.models import Users
from django.db.models import Q


# все для Rest Api
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView

# serializers
from bmstu_lab_m.serializers import CargoSerializer
from bmstu_lab_m.serializers import OrdersSerializer
# from bmstu_lab_m.serializers import Cargo_Order_Serializer

from drf_yasg.utils import swagger_auto_schema
from django.utils.text import slugify
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.http import HttpRequest

from django.db.models import Q, F
from drf_yasg import openapi

from django.http import JsonResponse
from rest_framework.decorators import api_view
import hashlib
import secrets
from django.utils import timezone
import requests
from django.http import JsonResponse
import psycopg2

'''Заявки на доставку грузов на Марс на Starship. 
Услуги - товары, доставляемыe на Марс на Starship, 
   заявки - заявки на конкретный объем товаров
'''
import redis

#sudo service redis-server start
def get_instance_redis():
    red =  redis.Redis(
        host='0.0.0.0',
        port=6379,
    )
    return red


def set_key(key, value):
    red = get_instance_redis()
    red.set(key, value, ex=86400)


def get_value(key):
    red = get_instance_redis()
    return red.get(key)


def delete_value(key):
    red = get_instance_redis()
    red.delete(key)

ID_USER = 5
MODERATOR_ID = 6



def check_user(request):
    response = login_view_get(request._request)
    if response.status_code == 200:
        user = Users.objects.get(id_user=response.data.get('id_user').decode())
        return user.is_moderator == False
    return False


def check_moderator(request):
    response = login_view_get(request._request)
    print(response)
    if response.status_code == 200:
        user = Users.objects.get(id_user=response.data.get('id_user'))
        print(user.is_moderator,'check moder')
        return user.is_moderator == True
    
    return False




def check_authorize_get(request):
    response = login_view_get(request._request)
    if response.status_code == 200:
        user = Users.objects.get(id_user=response.data.get('id_user'))
        print(f'User in check_authorize: {user}')
        return user
    return None
def check_authorize(request):
    response = login_view(request._request)
    # print(response)
    if response.status_code == 200:
        user = Users.objects.get(id_user=response.data.get('id_user'))
        # print(f'User in check_authorize: {user}')
        return user
    return None
#ser Domain
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['first_name', 'last_name', 'email',  'passwd'], #'login',
        properties={
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Фамилия пользователя'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Электронная почта пользователя'),
            # 'login': openapi.Schema(type=openapi.TYPE_STRING, description='Логин пользователя'),
            'passwd': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль пользователя'),
            # 'is_moderator' : openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Пользователь является модератором?'),
        }
    ),
    responses={
        201: openapi.Response(description='Пользователь успешно создан'),
        400: openapi.Response(description='Не хватает обязательных полей или пользователь уже существует'),
    },
    operation_description='Регистрация нового пользователя',
)
@api_view(['POST'])
def registration(request, format=None):
    required_fields = ['first_name', 'last_name', 'email',  'passwd',]#''login',is_moderator']
    missing_fields = [field for field in required_fields if field not in request.data]

    if missing_fields:
        return Response({'Ошибка': f'Не хватает обязательных полей: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)

    if Users.objects.filter(email=request.data['email']).exists():
        return Response({'Ошибка': 'Пользователь с таким email уже существует'}, status=status.HTTP_400_BAD_REQUEST)

    password_hash = hashlib.sha256(f'{request.data["passwd"]}'.encode()).hexdigest()

    # try:
    Users.objects.create(
        first_name=request.data['first_name'],
        last_name=request.data['last_name'],
        email=request.data['email'],
        # login=request.data['login'],
        passwd=password_hash,
        # is_moderator=request.data['is_moderator'],
    )
    # except:
    #     return Response({'Ошибка': f'Не удалось создать пользователя'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Почта пользователя'),
            'passwd': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль пользователя'),
            # 'is_moderator': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Является ли пользователь модератором?'),
            
        },
        required=['email', 'passwd'],
    ),
    responses={
        200: openapi.Response(description='Успешная авторизация', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'id_user': openapi.Schema(type=openapi.TYPE_INTEGER)})),
        400: openapi.Response(description='Неверные параметры запроса или отсутствуют обязательные поля'),
        401: openapi.Response(description='Неавторизованный доступ'),
    },
    operation_description='Метод для авторизации',
)
@api_view(['POST','PUT','DELETE'])
def login_view(request, format=None):
    existing_session = request.COOKIES.get('session_key')
    if existing_session and get_value(existing_session):
        return Response({'id_user': get_value(existing_session)})

    email_ = request.data.get("email")
    password = request.data.get("passwd")

    if not email_ or not password:
        return Response({'error': 'Необходимы почта и пароль'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Users.objects.get(email=email_)
    except Users.DoesNotExist:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    password_hash = hashlib.sha256(f'{password}'.encode()).hexdigest()

    if password_hash == user.passwd:
        random_part = secrets.token_hex(8)
        session_hash = hashlib.sha256(f'{user.id_user}:{email_}:{random_part}'.encode()).hexdigest()
        set_key(session_hash, user.id_user)

        response = JsonResponse({'first_name': user.first_name, "last_name" : user.last_name, 'id_user': user.id_user, 'is_moderator' : user.is_moderator})
        response.set_cookie('session_key', session_hash, max_age=86400)
        return response

    return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
def login_view_get(request, format=None):
    existing_session = request.COOKIES.get('session_key')
    if existing_session and get_value(existing_session):
        return Response({'id_user': get_value(existing_session)})
    return Response(status=status.HTTP_401_UNAUTHORIZED)


@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(description='Успешный выход', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'message': openapi.Schema(type=openapi.TYPE_STRING)})),
        401: openapi.Response(description='Неавторизованный доступ', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING)})),
    },
    operation_description='Метод для выхода пользователя из системы',
)
@api_view(['GET'])
def logout_view(request):
    session_key = request.COOKIES.get('session_key')

    if session_key:
        if not get_value(session_key):
            return JsonResponse({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)
        delete_value(session_key)
        response = JsonResponse({'message': 'Вы успешно вышли из системы'})
        response.delete_cookie('session_key')
        return response
    else:
        return JsonResponse({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)




@swagger_auto_schema(
    method='GET',
    manual_parameters=[
        openapi.Parameter('search', openapi.IN_QUERY, description='Поле для поиска по названию', type=openapi.TYPE_STRING),
        openapi.Parameter('filter', openapi.IN_QUERY, description='Фильтр ("weight" или "title")', type=openapi.TYPE_STRING),
    ],
    responses={
        200: CargoSerializer(many=True),
        403: 'Доступ запрещен',
        400: 'Ошибка запроса',
    },
    operation_description='GET метод получения услуг'
)
@api_view(['GET'])
def cargo_list(request, format=None):
    """
    Список грузов с фильтрацией
    """
    user = check_authorize_get(request)
    how_to_filter = request.GET.get('filter', None)
    if_search = request.GET.get('search', None)

    

    if how_to_filter is not None:
        if how_to_filter == 'weight' or how_to_filter == 'title':
            cargos = Cargo.objects.all().filter(is_deleted=False).order_by(f'{how_to_filter}')
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        cargos = Cargo.objects.all().filter(is_deleted=False)

    if if_search is not None:
        cargos = Cargo.objects.all().filter(is_deleted=False, title__icontains=f'{if_search}')
    else:
        cargos = Cargo.objects.all().filter(is_deleted=False)

    serializer = CargoSerializer(cargos, many=True)

    serializer_data = serializer.data
    
    response_data = {
        'data': serializer_data,
       
    }

    if user:
        id_user = user.id_user

        data = DeliveryOrders.objects.filter(id_user=id_user, order_status='введён')

        try:
            id_order_draft = data[0].id_order
        except IndexError:
            id_order_draft = None

        response_data[ 'id_order_draft'] =  id_order_draft
    return Response(response_data)



from django.core.files.base import ContentFile

@swagger_auto_schema(
    method='POST',
    request_body=CargoSerializer,
    responses={
        201: CargoSerializer(),
        403: 'Доступ запрещен',
        400: 'Неправильный запрос',
    },
    operation_description='Добавление нового груза'
)

@api_view(['POST'])
def add_cargo(request, format=None):
    """
    Добавление нового груза
    """
    user = check_authorize(request)
    if not user or not user.is_moderator:
        return Response(status=status.HTTP_403_FORBIDDEN)

    cargo_data = {
        "title": request.data.get("title", ""),
        "weight": request.data.get("weight", 0),
        "description": request.data.get("description", ""),
        "is_deleted": False,
    }

    if 'image_binary' in request.FILES:
        image_file = request.FILES['image_binary']
        cargo_data['image_binary'] = image_file.read()
    else:
        # cargo_data['image_binary']= new_method('/home/ilya/Рабочий стол/BMSTU/5 semester/WEB/bmstu_lab/bmstu_lab_m/default.jpg')
        try:
            cargo_data['image_binary']= new_method('/home/ilya/Рабочий стол/BMSTU/5 semester/WEB/bmstu_lab/bmstu_lab_m/default.jpg')
        except:
            print()
            return Response(status=status.HTTP_400_BAD_REQUEST)
    cargo_instance = Cargo.objects.create(**cargo_data)
    serializer = CargoSerializer(cargo_instance)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

def new_method(bi_image_path):
    with open(bi_image_path, 'rb') as file:
        binary_data = file.read()
    return binary_data
    


from datetime import datetime

@api_view(['GET'])
@swagger_auto_schema(
    responses={
        200: CargoSerializer(),
        404: 'Не найдено',
    },
    operation_description='Получить информацию о конкретном грузе'
)
def get_cargo(request, pk, format=None):
    """
    Получить информацию о конкретном грузе
    """
    cargo = Cargo.objects.filter(id_cargo=pk, is_deleted=False).first()

    if cargo is not None:
        serializer = CargoSerializer(cargo)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@swagger_auto_schema(
    responses={
        201: 'Создан',
        403: 'Доступ запрещен',
        404: 'Ошибка',
    },
    operation_description='Добавление заявки в заказ. Если заказ не создан, он создается'
)
def add_cargo_to_order(request, pk, format=None):
    """
        Добавление заявки в заказ. Если заказ не создан, он создается

        В итоге создается заявка, у которой есть создатель, но пока нет модератора
    """
    user = check_authorize(request)
    
    if not user: # or not user.is_moderator:
        return Response(status=status.HTTP_403_FORBIDDEN)

    ind_user = user.id_user
    user_instance = get_object_or_404(Users, pk=ind_user)
    cargo_instance = get_object_or_404(Cargo, pk=pk)

    order = DeliveryOrders.objects.filter(id_user=user_instance, order_status='введён')

    if not order.exists():
        order_to_add = DeliveryOrders.objects.create(id_user=user_instance, 
                                                    #  id_moderator=user_instance,
                                                     order_status='введён',
                                                     date_create=datetime.now())
        order_to_add.save()
        order_instance = order_to_add
    else:
        order_instance = order[0]

    try:
        CargoOrder.objects.create(id_cargo=cargo_instance, id_order=order_instance, amount=1)
    except:
        pass

    return Response(status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@swagger_auto_schema(
    request_body=CargoSerializer,
    responses={
        200: CargoSerializer(),
        400: 'Неправильный запрос',
        403: 'Доступ запрещен',
        404: 'Не найдено',
    },
    operation_description='Редактирование информации о грузе (только для модераторов)'
)
def edit_cargo(request, pk, format=None):
    """
    Редактирование информации о грузе (только для модераторов)
    """
    user = check_authorize(request)
    if not user or not user.is_moderator:
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    try:
   
        cargo_instance = Cargo.objects.get(pk=pk)
        

        cargo_instance.title = request.data.get("title", cargo_instance.title)
        cargo_instance.weight = request.data.get("weight", cargo_instance.weight)
        cargo_instance.description = request.data.get("description", cargo_instance.description)
        
       
        if 'image_binary' in request.FILES:
            image_file = request.FILES['image_binary']
            cargo_instance.image_binary = image_file.read()

        
        cargo_instance.save()


        serializer = CargoSerializer(cargo_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Cargo.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    except Exception as e:

        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@swagger_auto_schema(
    responses={
        200: 'OK',
        403: 'Доступ запрещен',
        404: 'Не найдено',
    },
    operation_description='Удаление груза через изменение статуса'
)
def delete_cargo(request, pk, format=None):
    """
    Удаление груза через изменение статуса
    """
    user = check_authorize(request)
    print(f'delete cargo/id/ for user {user}')

    if not user or not user.is_moderator:
        return Response(status=status.HTTP_403_FORBIDDEN)

    del_item = get_object_or_404(Cargo, pk=pk)
    del_item.is_deleted = True
    del_item.save()

    print(del_item)
    return Response(status=status.HTTP_200_OK)
        

# @api_view(['Put'])
# def put_detail(request, pk, format=None):
#     """
#     Обновляет информацию о грузe (для пользователя)
#     """
#     #no user, why
#     cargo = get_object_or_404(Cargo, pk=pk)
#     serializer = CargoSerializer(cargo, data=request.data, partial=True)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.utils.dateparse import parse_date


@swagger_auto_schema(
    method='GET',
    manual_parameters=[
        openapi.Parameter('order_status',
                          openapi.IN_QUERY,
                          description="Статус заявки для фильтрации",
                          type=openapi.TYPE_STRING),
        openapi.Parameter('date_create',
                          openapi.IN_QUERY,
                          description="Дата создания заявки",
                          type=openapi.TYPE_STRING,
                          format=openapi.FORMAT_DATE),
        openapi.Parameter('date_finished',
                          openapi.IN_QUERY,
                          description="Дата завершения заявки",
                          type=openapi.TYPE_STRING,
                          format=openapi.FORMAT_DATE),
    ],
    responses={
        200: OrdersSerializer(many=True),
        403: 'Доступ запрещен',
    },
    operation_description='GET списка заявок'
    
)
@api_view(['GET'])
def get_orders(request, format=None):
    """
    Список заказов пользователя (для обычного пользователя)
    Список заказов всех пользователей (для модератора)


    SELECT Delivery_orders.id_order ,Delivery_orders.order_status, Delivery_orders.id_user, Delivery_orders.id_moderator,Cargo.id_cargo , cargo.title
        FROM Delivery_orders
        INNER JOIN Cargo_Order ON Delivery_orders.id_order = Cargo_order.id_order
        INNER JOIN Cargo ON Cargo_order.id_cargo = Cargo.id_cargo
		order by Delivery_orders.id_order;
    """
    user = check_authorize_get(request)
    
    if not user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    id_user = user.id_user
    date_create = request.GET.get('date_create', None)
    # date_accept = request.GET.get('date_accept', None)
    date_finish = request.GET.get('date_finished', None)
    orderStatus = request.GET.get('order_status', None)

    if date_create:
        date_create = datetime.strptime(date_create, '%d.%m.%Y').date()
    if date_finish:
        date_finish = datetime.strptime(date_finish, '%d.%m.%Y').date()
  

    possible_statuses = ['в работе', 'завершён', 'отменён']
    if user.is_moderator != True:
        all_orders = DeliveryOrders.objects.filter(id_user=id_user, order_status__in=possible_statuses).order_by('-id_order')

        if orderStatus is not None:
            all_orders = all_orders.filter(id_user=id_user, order_status=orderStatus)

        if date_create is not None:
            if date_finish is not None:
                all_orders = all_orders.filter(id_user=id_user, date_create__gte=date_create, date_finish__lte=date_finish)
            else:
                all_orders = all_orders.filter(id_user=id_user, date_create__gte='1980-01-01')

        data = []
        
        for order in all_orders:
            user_instance = Users.objects.get(id_user=order.id_user.id_user)
            
            moderator_instance = None
            if order.id_moderator is not None:
                moderator_instance = Users.objects.get(id_user=order.id_moderator.id_user)
                

            data.append({
                "pk": order.pk,
                "id_order": order.id_order,
                "user_email": user_instance.email,
                "moderator_email": moderator_instance.email if moderator_instance is not None else None,
                "order_status": order.order_status,
                "is_delivered" : order.is_delivered,
                "date_create": order.date_create,
                "date_accept": order.date_accept,
                "date_finish": order.date_finish
            })
    else:
        all_orders = DeliveryOrders.objects.filter( order_status__in=possible_statuses).order_by("-id_order")
        
        
        if orderStatus is not None:
            all_orders = all_orders.filter( order_status=orderStatus)
        
        if date_create is not None:
            if date_finish is not None:
                all_orders = all_orders.filter( date_accept__gte=date_create, date_accept__lte=date_finish)
            else:
                all_orders = all_orders.filter(  date_accept__lte=date_finish)
        
        data = []
        for order in all_orders:
            user_instance = Users.objects.get(id_user=order.id_user.id_user)
            
            moderator_instance = None
            if order.id_moderator is not None:
                moderator_instance = Users.objects.get(id_user=order.id_moderator.id_user)
                
                
            data.append({
                "pk": order.pk,
                "id_order": order.id_order,
                "user_email": user_instance.email,
                "moderator_email": moderator_instance.email if moderator_instance is not None else None,
                "order_status": order.order_status,
                 "is_delivered" : order.is_delivered,
                "date_create": order.date_create,
                "date_accept": order.date_accept,
                "date_finish": order.date_finish
            })
    return Response(data)


    


@api_view(['GET'])
@swagger_auto_schema(
    responses={
        200: OrdersSerializer,
        403: 'Доступ запрещен',
        404: 'Данные не найдены',
    },
    operation_description='Get метод для конкретного заказа пользователя, со списком грузов внутри'
)
def get_order_detail(request, pk, format=None):
    user = check_authorize_get(request)

    if not user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    order = get_object_or_404(DeliveryOrders, pk=pk)
    serializer = OrdersSerializer(order)

    response_data = serializer.data

    # Get CargoOrder instances related to the order
    cargo_in_order_qs = CargoOrder.objects.filter(id_order=pk).order_by("id_cargo")

    # Build a list of cargo information including the amount from CargoOrder
    cargo_in_order_list = []
    for cargo_order in cargo_in_order_qs:
        cargo = Cargo.objects.get(pk=cargo_order.id_cargo.pk)
        cargo_data = CargoSerializer(cargo).data
        cargo_data['amount'] = cargo_order.amount  # Include the amount in the response
        cargo_in_order_list.append(cargo_data)

    response_data['Cargo_in_Order'] = cargo_in_order_list

    return Response(response_data, status=status.HTTP_200_OK)


from datetime import datetime
import dateutil.parser



@api_view(['PUT'])
@swagger_auto_schema(
    responses={
        200: OrdersSerializer,
        400: 'Неправильный запрос',
        403: 'Доступ запрещен',
        404: 'Не найдено',
    },
    operation_description='обновление информации о конкретном заказе'
)
def put_order_detail(request, pk, format=None):
  """
  Обновление информации о конкретном заказе
  """
  user = check_authorize(request)
  if not user: 
      return Response(status=status.HTTP_403_FORBIDDEN)

  order = get_object_or_404(DeliveryOrders, pk=pk)

  # Check if date_finish exists in request.data
#   if 'date_finish' in request.data:
#       # Convert date_finish to datetime object
#       date_finish = dateutil.parser.parse(request.data['date_finish'])
#       # Update date_finish in request.data
#       request.data['date_finish'] = date_finish

  # Update order attributes directly
  for key, value in request.data.items():
      setattr(order, key, value)

  try:
      # Save the updated order
      order.save()
      return Response({"message": "Order updated successfully"}, status=status.HTTP_200_OK)
  except Exception as e:
      return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@swagger_auto_schema(
    responses={
        200: 'OK',
        400: 'Неправильный запрос',
        403: 'Доступ запрещен',
        404: 'Не найдено',
    },
    operation_description='Удалить конкретный заказ'
)
def delete_order_detail(request, pk, format=None):
    """
    Удалить конкретный заказ
    """
    user = check_authorize(request)
    if not user: # or user.is_moderator:
        print(f'DELETE order/id for {user} failed')
        return Response(status=status.HTTP_403_FORBIDDEN)

    order = get_object_or_404(DeliveryOrders, pk=pk, id_user=user.id_user)
    curr_status = order.order_status
    if curr_status != 'введён':
        return Response(
            {"error": "удалить можно только черновую заявку"},
            status=status.HTTP_400_BAD_REQUEST
        )
    order.order_status = 'удалён'
    order.date_finish = datetime.now()
    order.save()

    return Response(status=status.HTTP_200_OK)





@swagger_auto_schema(
    method='PUT',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'status': openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Новый статус заявки",
                # enum=['в работе', 'отменён'],
            ),
        },
        required=['status'],
    ),
    responses={
        204: openapi.Response(description='Status updated successfully'),
        400: openapi.Response(description='Неправильный запрос'),
        403: openapi.Response(description='Доступ запрещен'),
    },
    operation_description='Update user status',
)
@api_view(['PUT'])
def set_user_status(request, pk, format=None):
    """
    Обновление статуса заказа пользователем
    в работе -> отменён
    введён -> в работе
    """
    user = check_authorize(request)
    if not user:# or user.is_moderator:
        print(f'set_user_status if failed for {user}')
        return Response(status=status.HTTP_403_FORBIDDEN)

    id_user = user.id_user
    data = request.data

    if 'status' not in data:
        return Response({"Ошибка": "\'status\' отсутствует в теле запроса"}, status=status.HTTP_400_BAD_REQUEST)

    new_status = data['status']
    if new_status not in ['в работе', 'отменён']:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    queryset = DeliveryOrders.objects.filter(id_user=id_user, order_status='введён' if new_status == 'в работе' else 'в работе')
    if new_status == "в работе":
        queryset = DeliveryOrders.objects.filter(id_user=id_user, order_status='введён')
        if queryset.exists():
            queryset.update( order_status=new_status ,date_accept =datetime.now())
            # Extract session_id from the request headers
        print(request.COOKIES.get('session_key'))
        session_id = request.COOKIES.get('session_key') #request.headers.get('Cookie', '').split('=')[2]
        print(session_id )
        # print(request.headers.get('Cookie', '').split('session_key=')[0].split(';')[0] )
        # Make a request to the /async_task endpoint
        async_task_url = "http://localhost:8000/api/async_task/"
        async_task_headers = {'Content-Type': 'application/json', 'Cookie': f'session_id={session_id}'}
        async_task_data = {"id_order": pk, "id_moderator" : user.id_user}
        async_task_response = requests.put(async_task_url, headers=async_task_headers, json=async_task_data)

        if async_task_response.status_code == 200:
            print(async_task_response)
            return Response(status=status.HTTP_204_NO_CONTENT)
    elif new_status == 'отменён': 
        queryset = DeliveryOrders.objects.filter(id_user=id_user, order_status='введён')
        if queryset.exists():
            queryset.update( date_finish=datetime.now(), order_status=new_status)
            return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        return Response({"Ошибка": "Заказ с указанным статусом не найден"}, status=status.HTTP_400_BAD_REQUEST)



        





@swagger_auto_schema(
    method='PUT',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'status': openapi.Schema(type=openapi.TYPE_STRING, description='New status (завершён or отменён)'),
        },
        required=['status'],
    ),
    responses={
        204: openapi.Response(description='Status updated successfully'),
        400: openapi.Response(description='Неправильный запрос'),
        403: openapi.Response(description='Доступ запрещен'),
    },
    operation_description='Обновить статус модератором',
)
@api_view(['PUT'])

def update_moderator_status(request, pk, format=None):
    """
    Возможные статусы:

    в работе -> завершён
    в работе -> отменён
    """
    user = check_authorize(request)
    if not user or not user.is_moderator:
        return Response(status=status.HTTP_403_FORBIDDEN)

    id_user = user.id_user
    data = request.data
    print(data)
    if 'status' not in data:
        return Response({"Ошибка": "\'status\' отсутствует в теле запроса"}, status=status.HTTP_400_BAD_REQUEST)

    new_status = data['status']
    if new_status not in ['завершён', 'отменён']:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    queryset = DeliveryOrders.objects.filter(id_order=pk, order_status='в работе')
    print(queryset)
    if queryset.exists():
        queryset.update(id_moderator=id_user, date_finish=datetime.now(), order_status=new_status)

        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    else:
        return Response({"Ошибка": "Заказ с указанным статусом не найден"}, status=status.HTTP_400_BAD_REQUEST)
    




@swagger_auto_schema(
    method='DELETE',
    responses={
        204: 'Успешно',
        403: 'Доступ запрещен',
        404: 'Найдено',
    },
    operation_description='Удалить услугу из заявки для пользователя'
)
@api_view(['DELETE'])
def delete_cargo_order(request, pk, format=None):
    """
    pk - номер груза (cargo), который мы хотим удалить из заказа 
    Удаляет груз из активного заказа
    Если груз был последний, удаляется и сам заказ
    """
    user = check_authorize(request)
    if not user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    id_user = user.id_user

    active_order = DeliveryOrders.objects.filter(order_status='введён', id_user=id_user).first()
    if active_order is not None:
        del_result = CargoOrder.objects.filter(
            id_order=active_order.id_order, id_cargo=pk
        ).delete()


    # Now check if there are any cargos left in the active order
    cargo_in_order_ids = CargoOrder.objects.filter(id_order=active_order.id_order)
    list_of_cargo_ids = [i.id_cargo.id_cargo for i in cargo_in_order_ids]
    cargo_in_order = Cargo.objects.filter(id_cargo__in=list_of_cargo_ids)

    cargo_serializer = CargoSerializer(cargo_in_order, many=True)
    
    try:
        cargo_in_active_order = cargo_serializer.data
    except ValueError:
        cargo_in_active_order = []

    

    if len(cargo_in_active_order) == 0:
        
        order = active_order
        curr_status = order.order_status
        if curr_status != 'введён':
            return Response(
                {"error": "удалить можно только черновую заявку"},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.order_status = 'удалён'
        order.date_finish = datetime.now()
        order.save()
        
    return Response(status=status.HTTP_204_NO_CONTENT)






@swagger_auto_schema(
    method='PUT',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'amount': openapi.Schema(type=openapi.TYPE_INTEGER, description='New amount'),
        },
        required=['amount'],
    ),
    responses={
        204: 'Amount updated successfully',
        403: 'Доступ запрещен',
        404: 'Не найдено',
    },
    operation_description='Обновляет количество для определенного груза в заказе '
)
@api_view(['PUT'])
def update_cargo_order_amount(request, pk, format=None):
    """
    Меняет значение количества для определенного груза
    Может быть только статус 'введён', потому что менять можно только черновую заявку
    """
    user = check_authorize(request)
    if not user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    id_user = user.id_user

    new_amount = request.data.get('amount')
    print(new_amount)
    active_order = DeliveryOrders.objects.filter(
        Q(order_status='введён'), id_user=id_user  #| Q(order_status='в работе'), 
    )
    print(active_order)
    if active_order.exists():
        CargoOrder.objects.filter(
            id_order=active_order[0].id_order, id_cargo=pk
        ).update(amount=new_amount)

        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(status=status.HTTP_404_NOT_FOUND)
    


    #!!!!!
@swagger_auto_schema(
    method='PUT',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        
    ),
    responses={
        204: 'Amount updated successfully',
        403: 'Доступ запрещен',
        404: 'Не найдено',
    },
    operation_description=''
)
@api_view(['PUT'])
def async_task(request, format=None):
    # user = check_authorize(request)
    # if not user:
    #     return Response(status=status.HTTP_403_FORBIDDEN)
    
    idOrder = request.data.get("id_order")
    if idOrder is None:
        return Response({"error": "id_order not provided"}, status=status.HTTP_400_BAD_REQUEST)
    

    order = get_object_or_404(DeliveryOrders, pk=idOrder)
    data = {"order_status" : 'завершён',
            "id_moderator" : request.data.get('id_moderator') }
    serializer = OrdersSerializer(order, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        print('is_valid')
    
    

    session_key = request.headers.get('Cookie')[11:]
    print(session_key)
    # Make a request to localhost:8080
    url = "http://localhost:8080/deliver/"
    headers = {'Content-Type': 'application/json'}
    # Include session_key in the data payload
    data = {"id_order": idOrder, "session_key": session_key}
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print(response)
        return Response(status=status.HTTP_200_OK)
    else:
        print(response)
        return Response(status=status.HTTP_404_NOT_FOUND)
