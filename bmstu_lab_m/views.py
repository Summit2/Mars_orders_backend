

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import psycopg2

from bmstu_lab_m.models import Cargo
#from bmstu_lab_m.models import CargoOrder
#from bmstu_lab_m.models import DeliveryOrders
#from bmstu_lab_m.models import Users



'''Заявки на доставку грузов на Марс на Starship. 
Услуги - товары, доставляемыe на Марс на Starship, 
   заявки - заявки на конкретный объем товаров
'''



def GetAllCargo(request):
    


    res=[]
    input_text = request.GET.get("good_item")
    data = Cargo.objects.filter(is_deleted=False)
    
    if input_text is not None:
        for elem in data:
        
            if input_text in elem.title:
                res.append(elem)
                #print(elem)
        return render(
        request,'all_cargo.html', {'data' : {
            'items' : res,
            'input' : input_text
        } }
                     )
    else:
    
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
    
    # result ={}
    # for i in arr:
    #     if i['id'] == id:
    #         result = i
    return render(request, 'current_cargo.html', 
        {'data' : {
        'item' : data[0]
    }}
    )


from django.urls import reverse

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
    

