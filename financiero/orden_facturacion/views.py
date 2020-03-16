from django.shortcuts import render,  redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from .models import OrdenFacturacion, Persona_Natural, Juridica, OrdenFacturacionParticipante, Contacto_natural
from .forms import OrdenFacturacionForm, OrdenFacturacionUpdateForm, OrdenFacturacionFinalForm, OrdenFacturacionParticipanteForm
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseRedirect
from datetime import date
from django.views.decorators.csrf import ensure_csrf_cookie
from .filters import OrdenFacturacionFilter
# Create your views here.

def index(request):
    if (request.GET.get('estado',None)!=None and 'ANLD' in request.GET['estado']):
        ordFac_lista = OrdenFacturacion.objects.all()
    else:
        ordFac_lista = OrdenFacturacion.objects.all().exclude(estado='ANLD')
    ordFac_filter = OrdenFacturacionFilter(request.GET, queryset=ordFac_lista)
    #ordFac_filter = OrdenFacturacionFilter(request.GET, queryset=OrdenFacturacion.objects.all())
    return render(request, "orden_facturacion.html", {"filter":ordFac_filter})

class OrdenFacturacionCreate(CreateView):
    model=OrdenFacturacion
    form_class=OrdenFacturacionForm
    template_name='orden_facturacion_nuevo.html'
    success_url=reverse_lazy('orden_facturacion')

    def form_valid(self, form):
        
        try:
            pre=str(int(self.model.objects.latest('pk').pk+1))
            sec='0'*(4-len(pre))+pre
        except self.model.DoesNotExist:
            sec='0001'      
        print("jojo")
        print(form.instance.contacto)
        print("jeje")
        form.instance.cod_orden_fact=sec+'-'+str(date.today().year)
        form.instance.valor_pendiente = form.instance.valor_total
        return super().form_valid(form)
    
    def get_success_url(self, **kwargs):         
        return reverse_lazy('orden_facturacion_editar', args = (self.object.id,))

    """def get_context_data(self, **kwargs):
        context=super(OrdenFacturacionCreate,self).get_context_data(**kwargs)
        context['form']=self.form_class()
        context['formn']=self.pn_form_class()
        context['formj']=self.pj_form_class()

        return context"""

class OrdenFacturacionUpdate(UpdateView):
    model=OrdenFacturacion
    form_class=OrdenFacturacionUpdateForm
    second_form_class=OrdenFacturacionForm
    third_form_class=OrdenFacturacionFinalForm
    participantes_class=OrdenFacturacionParticipante
    template_name='orden_facturacion_editar.html'
    success_url=reverse_lazy('orden_facturacion')

    def get_context_data(self, **kwargs):
        context=super(OrdenFacturacionUpdate,self).get_context_data(**kwargs)
        pk=self.kwargs.get('pk',0)
        orden=self.model.objects.get(id=pk)
        participantes=self.participantes_class.objects.filter(orden_id=pk)
        prueba=OrdenFacturacion.objects.all()
        for ori in prueba:
            print(ori.contacto)
        if 'form' in context:
            if orden.estado=='ACTV':
                print("actv")
                context['form']=self.second_form_class(instance=orden)
            elif orden.estado=='PNDP':
                print("pndp")
                context['form']=self.third_form_class(instance=orden)
            else:
                print("else")
                context['form']=self.form_class(instance=orden)
        context['orden_id']=pk
        #selected_participantes=[]
        #for par in orden.participantes.all():
        #    selected_participantes.append(par.pk)
        #context['selected_participantes']=selected_participantes
        #context['num']=list(range(0, orden.participantes.count()))
        context['participantes'] = participantes
        return context
    def form_valid(self, form):
        form.instance.valor_pendiente = form.instance.valor_total
        return super().form_valid(form)

class OrdenFacturacionDelete(DeleteView):
    model=OrdenFacturacion
    template_name='orden_facturacion_eliminar.html'
    success_url=reverse_lazy('orden_facturacion')
    form_class=OrdenFacturacionForm
      

def orden_fact_conf_elim(request):
    orden_id=request.GET.get('pk')
    orden=OrdenFacturacion.objects.get(id=orden_id)
    print(orden.tipo_cliente)
    form=OrdenFacturacionForm(instance=orden)
    return render(request,"orden_facturacion_eliminar.html",{"orden":orden,"form":form})



def cambiar_estado(request, pk):
    orden=OrdenFacturacion.objects.get(id=pk)
    orden.estado='SLCE'
    orden.save()
    return HttpResponseRedirect(reverse_lazy('orden_facturacion'))

def verificar_campos(request):
    return render(request,"orden_facturacion_confirmar.html")

def load_personas(request):
    persona = request.GET.get("persona")
    identificacion=[]
    razon_nombre=[]
    if persona=="Natural":
        personas=Persona_Natural.objects.all()
        print(personas)
        identificacion=render_to_string("dropdown_natural_ci.html",{"personas":personas})
        razon_nombre=render_to_string("dropdown_natural_nombres.html",{"personas":personas})
    elif persona=="Jurídica":
        personas=Juridica.objects.all()
        print(personas)
        identificacion=render_to_string("dropdown_juridica_ruc.html",{"personas":personas})
        razon_nombre=render_to_string("dropdown_juridica_razon.html",{"personas":personas})
    return JsonResponse({'ruc_ci': identificacion, 'razon_nombre': razon_nombre})

def load_contactos(request):
    id = request.GET.get("id")
    contactos=Contacto_natural.objects.filter(empresa=id)
    
    listnatid=[]
    for c in contactos:
        listnatid.append(c.contacto.cedula)
        
    contactosN=Persona_Natural.objects.filter(cedula__in=listnatid)
    
    contlist=render_to_string("dropdown_contacto.html",{"contactos":contactosN})  
    return JsonResponse({'contacto': contlist})

def load_info(request):
    id = request.GET.get("id")
    persona= request.GET.get("persona")
    direccion=""
    telefono=""
    contacto=""
    sector=""
    tipo=""
    ##Para Natural
    email =""
    celular = ""
    cargo = ""

    if id!="":
        if persona=="Natural":
            cliente=Persona_Natural.objects.get(pk=id)
            direccion=cliente.dir_domicilio
            telefono=cliente.tel_domicilio
            celular=cliente.celular
            email = cliente.email
            cargo = cliente.cargo
        elif persona=="Jurídica":
            print("si entra")
            cliente=Juridica.objects.get(ruc=id)
            #direccion= cliente.direccion
            #telefono= cliente.telefono
            sector= cliente.sector.nombre
            tipo= cliente.tipo_empresa.nombre

    return JsonResponse({'direccion': direccion, 'telefono': telefono, 'contacto': contacto, 'sector': sector, 'tipo': tipo,'email':email,'celular':celular,'cargo':cargo})

def load_info_veris(request):
    id = request.GET.get("id")
    persona= request.GET.get("persona")
    direccion=""
    telefono=""
    contacto=""
    sector=""
    tipo=""
    ##Para Natural
    email =""
    celular = ""
    cargo = ""

    if id!="":
        if persona=="Natural":
            cliente=Persona_Natural.objects.get(pk=id)
            direccion=cliente.dir_domicilio
            telefono=cliente.tel_domicilio
            celular=cliente.celular
            email = cliente.email
            cargo = cliente.cargo
        elif persona=="Jurídica":
            
            cliente=Juridica.objects.get(ruc=id)
            direccion= cliente.direccion
            telefono= cliente.telefono
            email= cliente.correo
            sector= cliente.sector.nombre
            tipo= cliente.tipo_empresa.nombre
    return JsonResponse({'direccion': direccion, 'telefono': telefono, 'contacto': contacto, 'sector': sector, 'tipo': tipo,'email':email,'celular':celular,'cargo':cargo})

def load_mail(request):
    cedula = request.GET.get("cedula")
    print(cedula)
    email=""
    if cedula!="":
        email=Persona_Natural.objects.get(cedula=cedula).email
    return JsonResponse({"email": email})

def load_usuarios_ventas(request):
    usuariosv=""
    asesores=render_to_string("dropdown_usuarios_ventas.html",{"usuariosv":usuariosv})  
    return JsonResponse({'asesores': asesores})

def load_info_ci(request):
    pk = request.GET.get("pk")
    ci=""
    if id!="":
        ci=OrdenFacturacion.objects.get(id=pk).ruc_ci
    return JsonResponse({'ci': ci})


class ParticipanteCreate(CreateView):
    model=OrdenFacturacionParticipante
    form_class=OrdenFacturacionParticipanteForm
    template_name='nuevo_participante.html'
    success_url='/financiero/orden_facturacion/editar'

    def get_context_data(self, **kwargs):
        context=super(ParticipanteCreate,self).get_context_data(**kwargs)
        pk=self.kwargs.get('pk',0)
        context['orden_id']=pk
        context['orden_cod']=OrdenFacturacion.objects.get(pk=pk).cod_orden_fact
        return context

    def post(self, request,*args,**kwargs):
        self.object =self.get_object
        form=self.form_class(request.POST)
        if form.is_valid():
            orden_id=kwargs['pk']
            p=form.save(commit=False)
            p.orden_id=orden_id
            p.save()
            return HttpResponseRedirect(self.get_success_url()+'/'+str(orden_id))
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ParticipanteUpdate(UpdateView):
    model=OrdenFacturacionParticipante
    form_class=OrdenFacturacionParticipanteForm
    template_name='nuevo_participante.html'
    success_url='/financiero/orden_facturacion/editar'

    def get_context_data(self, **kwargs):
        context=super(ParticipanteUpdate,self).get_context_data(**kwargs)
        pk=self.kwargs.get('fk',0)
        context['orden_id']=pk
        context['orden_cod']=OrdenFacturacion.objects.get(pk=pk).cod_orden_fact
        return context

    def post(self, request, *args, **kwargs):
        self.object=self.get_object
        orden_id=kwargs['fk']
        pk=kwargs['pk']
        participante=self.model.objects.get(id=pk)
        form=self.form_class(request.POST, instance=participante)
        if form.is_valid():
            p=form.save(commit=False)
            p.orden_id=orden_id
            p.save()
            return HttpResponseRedirect(self.get_success_url()+'/'+str(orden_id))
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ParticipanteDelete(DeleteView):
    model=OrdenFacturacionParticipante
    form_class=OrdenFacturacionParticipanteForm
    template_name='eliminar_participante.html'
    success_url='/financiero/orden_facturacion/editar'

    """def get_context_data(self, **kwargs):
        context=super(ParticipanteDelete,self).get_context_data(**kwargs)
        fk=self.kwargs.get('fk',0)
        context['orden_id']=fk
        context['orden_cod']=OrdenFacturacion.objects.get(pk=fk).cod_orden_fact
        return context
"""
    def post(self, request, *args, **kwargs):
        self.object=self.get_object()
        orden_id=kwargs['fk']
        self.object.delete()
        #p_id=kwargs['pk']
        #p=OrdenFacturacionParticipante.objects.get(id=p_id)
        #p.delete()
        return HttpResponseRedirect(self.get_success_url()+'/'+str(orden_id))

def participante_conf_elim(request):
    p_id=request.GET.get('pk')
    orden_id=request.GET.get('fk')
    p=OrdenFacturacionParticipante.objects.get(id=p_id)
    return render(request,"eliminar_participante.html",{"p":p, "orden_id":orden_id})

def aprobar_orden_facturacion(request, pk):
    if(request.method == 'POST'):
        p = get_object_or_404(OrdenFacturacion, pk=pk)
        p.estado="ACPF"
        p.save()
        return redirect('pendiente_aprobacion')
    else:
        p = get_object_or_404(OrdenFacturacion, pk=pk)
        form = OrdenFacturacionFinalForm(instance=p)
        participantes=OrdenFacturacionParticipante.objects.filter(orden_id=pk)
        return render(request, 'orden_facturacion_aprobar.html', {'form': form, 'participantes':participantes, "orden":p})


def anular_orden_facturacion(request, pk):
    if(request.method == 'POST'):
        p = get_object_or_404(OrdenFacturacion, pk=pk)
        p.estado="ANLD"
        motivo=dict(request.POST).get("motivo_anular")[0]
        p.motivo_anular=motivo
        p.save()
        return redirect('pendiente_aprobacion')
    else:
        p = get_object_or_404(OrdenFacturacion, pk=pk)
        form = OrdenFacturacionFinalForm(instance=p)
        participantes=OrdenFacturacionParticipante.objects.filter(orden_id=pk)
        return render(request, 'orden_facturacion_aprobar.html', {'form': form, 'participantes':participantes, "orden":p})