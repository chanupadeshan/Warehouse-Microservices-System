from datetime import datetime
from http import HTTPStatus
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.orm import Session

from .database import SessionLocal, engine
from .models import Base, Staff

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Staff Service", version="1.0.0")


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


class StaffBase(BaseModel):
	first_name: str
	last_name: str
	email: EmailStr
	phone: Optional[str] = None
	role: str
	department: str
	is_active: bool = True


class StaffCreate(StaffBase):
	pass


class StaffUpdate(BaseModel):
	first_name: Optional[str] = None
	last_name: Optional[str] = None
	email: Optional[EmailStr] = None
	phone: Optional[str] = None
	role: Optional[str] = None
	department: Optional[str] = None
	is_active: Optional[bool] = None


class StaffResponse(StaffBase):
	id: int
	created_at: datetime
	updated_at: datetime

	model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
	code: str
	title: str
	detail: str


class SuccessResponse(BaseModel):
	success: bool = True
	message: str
	data: object | None = None


class ErrorResponse(BaseModel):
	success: bool = False
	message: str
	error: ErrorDetail


def build_success_response(message: str, data: object | None = None, status_code: int = status.HTTP_200_OK):
	payload = {
		"success": True,
		"message": message,
		"data": data,
	}
	return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))


def build_error_response(status_code: int, message: str, detail: str):
	title = HTTPStatus(status_code).phrase
	payload = {
		"success": False,
		"message": message,
		"error": {
			"code": str(status_code),
			"title": title,
			"detail": detail,
		},
	}
	return JSONResponse(status_code=status_code, content=payload)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
	detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
	return build_error_response(exc.status_code, detail, detail)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_: Request, exc: RequestValidationError):
	validation_errors = []
	for err in exc.errors():
		location = ".".join(str(part) for part in err.get("loc", []))
		validation_errors.append(f"{location}: {err.get('msg', 'Invalid value')}")

	detail = "; ".join(validation_errors) if validation_errors else "Request validation failed"
	return build_error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, "Validation error", detail)


@app.get("/", response_model=SuccessResponse)
def health_check():
	return build_success_response("Staff service is running")


@app.post(
	"/staff",
	response_model=SuccessResponse,
	status_code=status.HTTP_201_CREATED,
)
def create_staff(staff: StaffCreate, db: Session = Depends(get_db)):
	existing_staff = db.query(Staff).filter(Staff.email == staff.email).first()
	if existing_staff:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="A staff member with this email already exists",
		)

	staff_record = Staff(**staff.model_dump())
	db.add(staff_record)
	db.commit()
	db.refresh(staff_record)
	staff_data = StaffResponse.model_validate(staff_record).model_dump(mode="json")
	return build_success_response("Staff member created successfully", staff_data, status.HTTP_201_CREATED)


@app.get("/staff", response_model=SuccessResponse)
def get_all_staff(
	skip: int = Query(default=0, ge=0),
	limit: int = Query(default=100, ge=1, le=500),
	db: Session = Depends(get_db),
):
	staff_records = db.query(Staff).offset(skip).limit(limit).all()
	staff_data = [StaffResponse.model_validate(staff).model_dump(mode="json") for staff in staff_records]
	return build_success_response("Staff members fetched successfully", staff_data)


@app.get("/staff/{staff_id}", response_model=SuccessResponse)
def get_staff(staff_id: int, db: Session = Depends(get_db)):
	staff_record = db.query(Staff).filter(Staff.id == staff_id).first()
	if not staff_record:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Staff member not found",
		)
	staff_data = StaffResponse.model_validate(staff_record).model_dump(mode="json")
	return build_success_response("Staff member fetched successfully", staff_data)


@app.put("/staff/{staff_id}", response_model=SuccessResponse)
def update_staff(staff_id: int, staff_update: StaffUpdate, db: Session = Depends(get_db)):
	staff_record = db.query(Staff).filter(Staff.id == staff_id).first()
	if not staff_record:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Staff member not found",
		)

	update_data = staff_update.model_dump(exclude_unset=True)

	if "email" in update_data:
		existing_staff = (
			db.query(Staff)
			.filter(Staff.email == update_data["email"], Staff.id != staff_id)
			.first()
		)
		if existing_staff:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="A staff member with this email already exists",
			)

	for key, value in update_data.items():
		setattr(staff_record, key, value)

	db.commit()
	db.refresh(staff_record)
	staff_data = StaffResponse.model_validate(staff_record).model_dump(mode="json")
	return build_success_response("Staff member updated successfully", staff_data)


@app.delete("/staff/{staff_id}", response_model=SuccessResponse)
def delete_staff(staff_id: int, db: Session = Depends(get_db)):
	staff_record = db.query(Staff).filter(Staff.id == staff_id).first()
	if not staff_record:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Staff member not found",
		)

	db.delete(staff_record)
	db.commit()
	return build_success_response("Staff member deleted successfully")
