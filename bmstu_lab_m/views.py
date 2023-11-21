
# django methods
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

# PostgreSQL
import psycopg2

# ORMs
from bmstu_lab_m.models import Cargo
from bmstu_lab_m.models import CargoOrder
from bmstu_lab_m.models import DeliveryOrders
#from bmstu_lab_m.models import DeliveryOrders
from bmstu_lab_m.models import Users

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

'''Заявки на доставку грузов на Марс на Starship. 
Услуги - товары, доставляемыe на Марс на Starship, 
   заявки - заявки на конкретный объем товаров
'''

conn = psycopg2.connect(
    dbname="starship_delivery",
    user="postgres",
    password="1111",
    host="localhost",
    port="5432"
)


def GetAllCargo(request):
    
    res=[]
    input_text = request.GET.get("good_item")
    data = Cargo.objects.filter(is_deleted=False)
    
    if input_text is not None:
        # for elem in data:
        
        #     if input_text in elem.title:
        #         res.append(elem)
        #         #print(elem)

        return render(
        request,'all_cargo.html', {'data' : {
            'items' : Cargo.objects.filter(is_deleted=False, title__contains=input_text),
            'input' : input_text
        } }
                     )
    
    return render(
            request,'all_cargo.html', {
                'data' :
                {
                    'items' : data
                }
            }
            
        )

def GetCurrentCargo(request, id):
    data = Cargo.objects.filter(id_cargo=id)
    
    return render(request, 'current_cargo.html', 
        {'data' : {
        'item' : data[0]
    }}
    )

@csrf_exempt
def DeleteCurrentCargo(request):
        if request.method == 'POST':
            
            id_del = request.POST.get('id_del') #работает,надо только бд прикрутить в all_cargo


            conn = psycopg2.connect(dbname="starship_delivery", host="127.0.0.1", user="postgres", password="1111", port="5432")
            cursor = conn.cursor()
            cursor.execute(f"update cargo set is_deleted = true where id_cargo = {id_del}")
            conn.commit()   # реальное выполнение команд sql1
            cursor.close()
            conn.close()

        redirect_url = reverse('all_cargo') 
        return HttpResponseRedirect(redirect_url)
    



class CargoList(APIView):
    model_class = Cargo
    serializer_class = CargoSerializer
    
    def get(self, request, format=None):
        """
        Возвращает список грузов
        """
        idUser = 2

        data = DeliveryOrders.objects.filter(id_user = idUser, order_status = 'введён')
        
        try:
            id_order_draft = data[0].id_order
        except IndexError:
            id_order_draft = None

        cargos = self.model_class.objects.all().order_by('weight')
        serializer = self.serializer_class(cargos, many=True)

        serializer_data = serializer.data

        # Return a dictionary containing the list of orders and the id_order_draft
        response_data = {
            'data': serializer_data,
            'id_order_draft': id_order_draft
        }

        return Response(response_data)
    def put(self, request, format=None):
        """
        Метод для фильтрации списка грузов
        """

        # Retrieve filter parameters from request data
        filter = request.data.get('filter')
        if filter == 'weight':
            cargos = self.model_class.objects.all().order_by('weight')
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Serialize and return the filtered orders
        serializer = self.serializer_class(cargos, many=True)
        serialized_data = serializer.data  

        return Response(serialized_data)
    

    def post(self, request, format=None):
        """
        Добавляет новый груз
        """
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            bi_image_path = request.data.get('image_binary')
            binary_data = self.new_method(bi_image_path)
            serializer.save(image_binary=binary_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def new_method(self, bi_image_path):
        with open(bi_image_path, 'rb') as file:
            binary_data = file.read()
        return binary_data
    
class CargoDetail(APIView):
    model_class = Cargo
    serializer_class = CargoSerializer
    users_class = Users
    
    def get(self, request, pk, format=None):
        """
        Возвращает информацию грузe
        """
        cargo = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(cargo)
        return Response(serializer.data)
    
    def post(self, request, pk, format=None):
        '''
        Добавление определенного груза в заявку 

        SELECT Delivery_orders.id_order, Cargo.id_cargo , cargo.title
        FROM Delivery_orders
        INNER JOIN Cargo_Order ON Delivery_orders.id_order = Cargo_order.id_order
        INNER JOIN Cargo ON Cargo_order.id_cargo = Cargo.id_cargo;
        
        '''
        ind_User = 2 #хардкод, потом надо будет убрать
        ind_Moderator = 1

        user_instance = get_object_or_404(Users, pk=ind_User)
        moderator_instance = get_object_or_404(Users, pk=ind_Moderator)
        cargo_instance = get_object_or_404(Cargo, pk=pk)
        
        order = DeliveryOrders.objects.all().filter(id_user=user_instance, id_moderator=moderator_instance, order_status = 'введён')
        
       
        if not order.exists():
            #здесь добавляем заказ, если его до этого не было
            # и присваиваем ему статус 'введён'
            order_to_add = DeliveryOrders.objects.create(id_user = user_instance,
                                                          id_moderator=moderator_instance, 
                                                          order_status = 'введён' )
            order_to_add.save()
            order = order_to_add


        # for i in order:
        #     print(i)
        order_instance = get_object_or_404(DeliveryOrders, pk = order[0].id_order)
            # и добавляем в таблицу многие ко многим

        try:
            many_to_many = CargoOrder.objects.create(id_cargo=cargo_instance, 
                                                        id_order=order_instance,
                                                        amount = 1) #amount пока 1, потом можно будет поменять
            many_to_many.save()
        except:
            # значит в таблице многие ко многим уже существует запись
            pass
        

        return Response(status=status.HTTP_201_CREATED)
        

    
        

    def put(self, request, pk, format=None):
        """
        Обновляет информацию о грузe(для модератора)
        """

        ind_Moderator = 1 # хардкод
        if Users.objects.all().filter(id_user = ind_Moderator)[0].is_moderator == True:
        

            cargo = get_object_or_404(self.model_class, pk=pk)
            serializer = self.serializer_class(cargo, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
        

    def delete(self, request, pk, format=None):
        """
        Удаляет запись груза логически(через статус)
        """
        del_item = get_object_or_404(self.model_class, pk=pk)
        del_item.is_deleted = True
        del_item.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
        

@api_view(['Put'])
def put_detail(request, pk, format=None):
    """
    Обновляет информацию о грузe (для пользователя)
    """
    cargo = get_object_or_404(Cargo, pk=pk)
    serializer = CargoSerializer(cargo, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.utils.dateparse import parse_date

class OrdersList(APIView):
    model_class = DeliveryOrders
    serializer_class = OrdersSerializer

   

    def get(self, request, format=None):
        """
        Возвращает список акций
        """
        idUser = 2
        all_orders = self.model_class.objects.filter(id_user = idUser)
        data = []
        for order in all_orders:
            user = Users.objects.get(id_user=order.id_user.id_user)
            moderator = Users.objects.get(id_user=order.id_moderator.id_user)
            data.append({
                "pk": order.pk,
                "id_order": order.id_order,
                "user_email": user.email,
                "id_moderator": moderator.id_user,
                "order_status": order.order_status,
                "date_create": order.date_create,
                "date_accept": order.date_accept,
                "date_finish": order.date_finish
            })
        return Response(data)


    def put(self, request, format=None):
        """
        Метод для фильтрации списка заявок
        """

        # Retrieve filter parameters from request data
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        status = request.data.get('status')

        # Convert date strings to datetime.date objects
        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else None

        # Get all orders
        all_orders = self.model_class.objects.all()

        # Filter orders by date if start_date and end_date are provided
        if start_date and end_date:
            all_orders = all_orders.filter(date_create__range=(start_date, end_date))

        # Filter orders by status if status is provided
        if status:
            all_orders = all_orders.filter(order_status=status)

        # Order by status and date
        all_orders = all_orders.order_by('order_status', 'date_create')

        # Serialize and return the filtered orders
        serializer = self.serializer_class(all_orders, many=True)
        serialized_data = serializer.data  # this is a list of dictionaries

        return Response(serialized_data)


class OrderDetail(APIView):
    model_class = DeliveryOrders
    serializer_class = OrdersSerializer
    
    def get(self, request, pk, format=None):
        """
        Возвращает информацию об акции
        """
        order = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(order)

        responce = serializer.data

        cargo_in_order_ids = CargoOrder.objects.filter(id_order = pk)
        list_of_cargo_ids = [i.id_cargo.id_cargo for i in cargo_in_order_ids]
        print(list_of_cargo_ids)
        cargo_in_order = Cargo.objects.filter(id_cargo__in = list_of_cargo_ids)

        print(cargo_in_order)

        cargo_serializer = CargoSerializer(cargo_in_order, many=True)

        responce['Cargo_in_Order'] = cargo_serializer.data
        return Response(responce)
    
    def put(self, request, pk, format=None):
        """
        Обновляет информацию об акции (для модератора)
        """
        order = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Меняет статус заказа на удалён
        Может делать только создатель
        """
        order = get_object_or_404(self.model_class, pk=pk)
        order.order_status = "удалён"
        order.save()  # Save the changes to the database
        return Response(status=status.HTTP_204_NO_CONTENT)




class UpdateUserStatus(APIView):
    model_class = DeliveryOrders
    serializer_class = OrdersSerializer
    def put(self, request, format=None):
        """
        Обновляет статус для пользователя
        """
        
        try:
            idUser = request.data.get('id_user')
            idModer = request.data.get('id_moderator')
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        self.model_class.objects.filter(id_user = idUser, id_moderator = idModer, order_status = 'введён').update(order_status = 'в работе')
        return Response(status=status.HTTP_204_NO_CONTENT)

        




class UpdateModeratorStatus(APIView):
    model_class = DeliveryOrders
    serializer_class = OrdersSerializer

    def put(self, request, format=None):
        """
        Обновляет статус для модератора
        """
        
        try:
            idUser = request.data.get('id_user')
            idModer = request.data.get('id_moderator')
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        order = self.model_class.objects.filter(id_user = idUser,id_moderator = idModer, order_status = 'в работе').update(order_status = 'завершён') #

        return Response(status=status.HTTP_204_NO_CONTENT)
