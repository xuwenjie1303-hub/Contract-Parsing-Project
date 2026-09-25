from app.model.contract import Contract,FieldResult
from pydantic import BaseModel,Field


#计算置信度
def check_output(result):
    for keyword in Contract.model_fields.keys():
        count=[0,0,0,0,0,0]
        i=0
        fr:Field = getattr(result,keyword)
        for key in FieldResult.model_fields.keys():
            if key != 'confidence' and key != 'description':
                l=getattr(fr,key)
                if l != None and l != "NOT_FOUND":
                    count[i] += 20
        fr.confidence = count[i]
        i += 1
