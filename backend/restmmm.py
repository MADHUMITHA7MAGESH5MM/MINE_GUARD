from model_service import model_service

result = model_service.predict(
    "Worker entered confined space without permit"
)

print(result)