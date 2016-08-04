CREATE TABLE Contactcontactorders_associationSalesOrder ("ContactSet_contactorders_association_ContactId" UUID NOT NULL, "SalesOrderSet_contactorders_association_SalesOrderId" UUID NOT NULL);
ALTER TABLE Contactcontactorders_associationSalesOrder (ADD CONSTRAINT "Contactcontactorders_associationSalesOrder_fkA" FOREIGN KEY ("ContactSet_contactorders_association_ContactId") REFERENCES "ContactSet"("ContactId"), ADD CONSTRAINT "Contactcontactorders_associationSalesOrder_fkB" FOREIGN KEY ("SalesOrderSet_contactorders_association_SalesOrderId") REFERENCES "SalesOrderSet"("SalesOrderId"), ADD CONSTRAINT "Contactcontactorders_associationSalesOrder_pk" UNIQUE ("ContactSet_contactorders_association_ContactId", "SalesOrderSet_contactorders_association_SalesOrderId"));
