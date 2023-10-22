
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
#from bmstu_lab_m.models import DeliveryOrders
#from bmstu_lab_m.models import Users

# все для Rest Api
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
# serializers
from bmstu_lab_m.serializers import CargoSerializer


'''Заявки на доставку грузов на Марс на Starship. 
Услуги - товары, доставляемыe на Марс на Starship, 
   заявки - заявки на конкретный объем товаров
'''



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
    



@api_view(['Get'])
def get_list(request, format=None):
    """
    Возвращает список грузов
    """
    print('get')
    cargo = Cargo.objects.all().filter(is_deleted = False)
    serializer = CargoSerializer(cargo, many=True)
    return Response(serializer.data)



@api_view(['Post'])
def post_list(request, format=None):    
    """
    Добавляет новый груз
    """
    print('post')
    serializer = CargoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['Get'])
def get_detail(request, pk, format=None):
    stock = get_object_or_404(Cargo, pk=pk)
    if request.method == 'GET':
        """
        Возвращает информацию о грузе
        """
        serializer = CargoSerializer(stock)
        return Response(serializer.data)

@api_view(['Put'])
def put_detail(request, pk, format=None):
    """
    Обновляет информацию о грузе
    """
    cargo= get_object_or_404(Cargo, pk=pk)
    serializer = CargoSerializer(cargo, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['Delete'])
def delete_detail(request, pk, format=None):    
    """
    Удаляет информацию о грузе
    """
    del_item = get_object_or_404(Cargo, pk=pk)
    del_item.is_deleted = True
    del_item.save()
    return Response(status=status.HTTP_204_NO_CONTENT)
    # id_del = request.POST.get('id_del') #работает,надо только бд прикрутить в all_cargo
    # conn = psycopg2.connect(dbname="starship_delivery", host="127.0.0.1", user="postgres", password="1111", port="5432")
    # cursor = conn.cursor()
    # cursor.execute(f"update cargo set is_deleted = true where id_cargo = {id_del}")
    # conn.commit()   # реальное выполнение команд sql1
    # cursor.close()
    # conn.close()

    

# from rest_framework.response import Response
# from django.shortcuts import get_object_or_404
# from rest_framework import status
# from stocks.serializers import StockSerializer
# from stocks.models import Stock

# from rest_framework.decorators import api_view

class StockList(APIView):
    model_class = Cargo
    serializer_class = CargoSerializer
    
    def get(self, request, format=None):
        """
        Возвращает список грузов
        """
        stocks = self.model_class.objects.all()
        serializer = self.serializer_class(stocks, many=True)
        return Response(serializer.data)
    
    def post(self, request, format=None):
        """
        Добавляет новый груз
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StockDetail(APIView):
    model_class = Cargo
    serializer_class = CargoSerializer

    def get(self, request, pk, format=None):
        """
        Возвращает информацию об акции
        """
        stock = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(stock)
        return Response(serializer.data)
    
    def put(self, request, pk, format=None):
        """
        Обновляет информацию об акции (для модератора)
        """
        stock = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(stock, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Удаляет информацию об акции
        """
        stock = get_object_or_404(self.model_class, pk=pk)
        stock.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@api_view(['Put'])
def put_detail(request, pk, format=None):
    """
    Обновляет информацию об акции (для пользователя)
    """
    stock = get_object_or_404(Stock, pk=pk)
    serializer = StockSerializer(stock, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)