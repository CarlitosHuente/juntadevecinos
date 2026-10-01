from unfold.forms import UserChangeForm, UserCreationForm

from cuentas.models import Usuario


class UsuarioCambioForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = "__all__"


class UsuarioAltaForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("username", "password1", "password2", "first_name", "last_name", "email", "junta", "groups")
