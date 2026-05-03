curl -X POST https://whatsapp-onboarding-production.up.railway.app/webhook/new-paid-member \
-H "Content-Type: application/json" \
-d '{
  "transaction_id": 99903,
  "first_name": "DolunayTest",
  "last_name": "TestA",
  "email": "testa@example.com"
}'

echo ""
sleep 2

curl -X POST https://whatsapp-onboarding-production.up.railway.app/webhook/membership-questions \
-H "Content-Type: application/json" \
-d '{
  "transaction_id": 99903,
  "first_name": "DolunayTest",
  "last_name": "TestA",
  "answer_1": "+905335273513"
}'

echo ""
