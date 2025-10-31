from fastapi import FastAPI, Path , HTTPException, Query    # Import FastAPI class
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()  # Create a FastAPI instance (object)

class Patient(BaseModel):

    id: Annotated[str, Field(..., description="The unique ID of the patient", example="P001")]
    name: Annotated[str, Field(..., description="Name of the patient")]
    city: Annotated[str, Field(..., description="City of the patient")]
    age: Annotated[int, Field(...,gt=0, lt=120, description="Age of the patient")]
    gender: Annotated[str, Literal['Male', 'Female', 'Other'], Field(..., description="Gender of the patient")]
    height: Annotated[float, Field(...,gt=0,description="Height of the patient in mtrs")]
    weight: Annotated[float, Field(...,gt=0, description= "Weight of the patient in Kg")]


    @computed_field
    @property
    def bmi(self) -> float:
        bmi = self.weight/(self.height ** 2)
        return round(bmi,2)

    @computed_field
    @property
    def verdict(self)->str:  # return health verdict based on BMI
            if self.bmi < 18.5:
                return "Underweight"
            elif 18.5 <= self.bmi <24.9:
                return "Normal weight"
            elif 25 <= self.bmi <29.9:
                return "Overweight"
            else:
                return "Obese"


class PatientUpdate(BaseModel):   # Model for updating patient details
    # All fields are optional for update
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(gt=0, lt=120, default=None)]
    gender: Annotated[Optional[str], Literal['Male', 'Female', 'Other'], Field(default=None)]
    height: Annotated[Optional[float], Field(gt=0,default=None)]
    weight: Annotated[Optional[float], Field(gt=0, default=None)]

def load_data():
    with open("patients.json", "r") as f:
        data = json.load(f)
    return data

def save_data(data):
    with open("patients.json","w") as f:
        json.dump(data, f)



@app.get("/")  # Define a route for the root URL
def hello():
    return {"message": "Patient Management System API"}



@app.get("/about")  # Define another route
def about():
    return {"message": "A fully functional API to manage your patients records."}



@app.get('/view')  # View all patients
def view():
    data = load_data()
    return data



@app.get('/patients/{patient_id}')  # View a specific patient by ID
def view_patient(patient_id: int = Path(..., description="The ID of the patient in the DB", example="1,..")):
    data = load_data()
    for patient in data:
        if patient["id"] == patient_id:
            return patient
        raise HTTPException(status_code=404, detail="Patient not found")



@app.get('/sort')  # Sort patients
def sort_patients(sort_by: str = Query(..., description="Sort on the basis of gender, age"),order: str = Query('asc',descrption="sort in asc or desc order")):

    valid_fields = ['gender','age']
    if sort_by not in valid_fields: # gender and age bahek aru input aayo vane
        raise HTTPException(status_code=400, detail=f"Invalid sort field. Valid fields are: {valid_fields}") # 400 means bad request
    
    if order not in ['asc','desc']:
        raise HTTPException(status_code=400, detail="Invalid order. Valid orders are: 'asc' or 'desc' ")
    
    data = load_data()

    sort_order = True if order == 'desc' else False

    sorted_data = sorted(data, key=lambda x: x.get(sort_by, 0), reverse= sort_order)
    
    return sorted_data



@app.post('/create')  # Create a new patient
def create_patient(patient: Patient):

    #load existing data
    data = load_data()

    #check if the patient already exists
    if patient.id in data:
        raise HTTPException(status_code = 400, detail="Patient already exists")
    

    #new patient add to the database
    data[patient.id] = patient.model_dump(exclude=["id"])  # exclude id field as it is the key


    #save the updated data back to the file
    save_data(data)

    return JSONResponse(status_code=201, content={"message":"Patient created sucessfully!"})



@app.put('/edit/{patient_id}')  # Update patient details
def update_patient(patient_id: str, patient_update: PatientUpdate):
    
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    existing_patient_info = data[patient_id]  # get existing patient details

    updated_patient_info = patient_update.model_dump(exclude_unset=True)  # get only provided fields for update

    for key, value in updated_patient_info.items():  # update existing details with new details
        existing_patient_info[key] = value  # update only provided fields
    
    #existing_patient_info -> pydantic object -> update bmi + verdict
    existing_patient_info['id'] = patient_id  
    patient_pydantic_obj = Patient(**existing_patient_info)  # create a pydantic object to recalculate computed fields
    
    # pydantic object -> dict
    existing_patient_info = patient_pydantic_obj.model_dump(exclude='id')
    
    # add this dict to data
    data[patient_id]= existing_patient_info # save back the updated patient info

    #save the data
    save_data(data)

    return JSONResponse(status_code=200, content= {'message': 'Patient details updated successfully!'})


@app.delete('/delete/{patient_id}')  # Delete a patient
def delete_patient(patient_id: str):

    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    del data[patient_id] # delete the patient

    save_data(data) # save the updated data

    return JSONResponse(status_code=200, content={'message':'Patient deleted successfully!'})