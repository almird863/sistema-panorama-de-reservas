from models.model_uh import (inserir_uh, deletar_uh)

apartamentos = [{
    "numeracao": "1",
    "vm": 1,
    "vr": 0,
    "acc": 0
},
{
    "numeracao": "2",
    "vm": 1,
    "vr": 0,
    "acc": 0
},
{
    "numeracao": "3",
    "vm": 1,
    "vr": 0,
    "acc": 1
},
{
    "numeracao": "4",
    "vm": 1,
    "vr": 0,
    "acc": 1
},
{
    "numeracao": "5",
    "vm": 0,
    "vr": 1,
    "acc": 0
},
{
    "numeracao": "6",
    "vm": 1,
    "vr": 0,
    "acc": 0
},
{
    "numeracao": "7",
    "vm": 1,
    "vr": 0,
    "acc": 0
},
{
    "numeracao": "8",
    "vm": 1,
    "vr": 0,
    "acc": 0
},
{
    "numeracao": "9",
    "vm": 1,
    "vr": 0,
    "acc": 0
},
{
    "numeracao": "10",
    "vm": 0,
    "vr": 1,
    "acc": 0
}]

for i in apartamentos:
    inserir_uh(i['numeracao'], i['vm'], i['vr'], i['acc'])