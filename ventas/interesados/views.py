from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.generic import CreateView,UpdateView,DeleteView
from django.core.exceptions import ValidationError
from .models import *
from .forms import *
from django.urls import reverse_lazy
from datetime import date
import threading
import queue
import os
# Create your views here.



class InteresadoCreate(CreateView):
	model=Interesado
	form_class=InteresadoForm
	template_name='interesado_form.html'
	success_url=reverse_lazy('interesados')

	def get_success_url(self, **kwargs):
			return reverse_lazy('interesados')


class InteresadoUpdate(UpdateView):
	model=Interesado
	form_class=InteresadoForm
	template_name='interesados_editar.html'
	success_url=reverse_lazy('interesados')

class InteresadoDelete(DeleteView):
	model=Interesado
	template_name='interesado_eliminar.html'
	success_url=reverse_lazy('interesados')
def interesado_conf_elim(request):

	interesado_id=request.GET.get('pk')
	interesado=Interesado.objects.get(pk=interesado_id)
	return render(request,"interesado_eliminar.html",{"interesado":interesado})
def cargar_personas_thread(f,q,formulario):
	campos = {"motivo_interes":"Motivo de interés","correo":"Correo","celular":"Celular","apellido":"Apellido","nombre":"Nombre"}
	if(f==None and f.lower().find(".csv")==-1):
		return
	fi = open(f,"r")
	c=0
	errores = 0
	for line in fi:
		data = line.strip().split("|")
		if(len(data)==6):
			interesado = Interesado()
			
			try:
				
				interesado.nombre=data[0]
				interesado.apellido = data[1]
				interesado.celular = data[2]
				interesado.correo = data[3]
				interesado.motivo_interes = data[5]
				interesado.canal_de_contacto = CanalContacto.objects.get(nombre=data[4])
				interesado.full_clean()
				interesado.save()	
				c+=1
			except ValidationError as e:
				c+=1
				errores+=1
				for i in e.error_dict:
					for j in e.error_dict[i]:
						error = str(j).strip("['']")
						formulario.add_error("archivo",forms.ValidationError("Problemas en la linea "+str(c)+ " con el " + campos[str(i)]  + ': '+ str(error)))
				pass
			except:
				c+=1
				errores+=1
				formulario.add_error("archivo",forms.ValidationError("Problemas en la linea " + str(c) + " con el Canal de contacto o un valor no válido"))
				pass
		else:
			c+=1
			errores+=1
			formulario.add_error("archivo",forms.ValidationError("Problemas en la linea " + str(c)+ " la cantidad de datos ingresados por fila es incorrecta"))

	q.put(errores)
	q.put(c)
	q.put("fin")		
	fi.close()
	os.remove(f)
def handle_uploaded_file(f,formulario):
	# _file = 'media/uploads/carga/'+str(f)
	_file = str(f)

	# if(os.path.isfile(_file)):
	# 	import random
	# 	_file='media/uploads/carga/'+str(random.randint(0,1000))+str(f)
	with open(_file, 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)
	valores_retorno = queue.Queue()
	t = threading.Thread(target=cargar_personas_thread,
							 args=(_file,valores_retorno,formulario))
	t.setDaemon(True)
	t.start()
	lineas =[]
	for valores in iter(valores_retorno.get, "fin"):
		lineas.append(valores)
	print(lineas)
	return lineas
	

def cargar_interesados(request):
	if request.method == 'POST':
	
		form = InteresadoCargarForm(request.POST, request.FILES)
		if form.is_valid():
			errores = handle_uploaded_file(request.FILES['archivo'],form)
			if(errores[0]==0):
				return HttpResponseRedirect(reverse_lazy('interesados'))
			else:
				if(errores[0]!=errores[1]):
					form.add_error("archivo",forms.ValidationError("El resto de interesados fueron creados exitosamente"))
	else:
		form = InteresadoCargarForm()
	return render(request, 'interesados_cargar.html', {'form': form})
