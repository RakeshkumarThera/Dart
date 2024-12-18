{
    "CreateAnalyticTables" : [
        "sql/CreateTableAX7.0/DDLGenDisplayTables {'testSuiteId':  '33', 'testCase': 'Create_Fact_Dimension_Table_DDL_Storage_Attribute'}",
        "sql/CreateTableAX7.0/DDLGenDisplayTableWithLogicalPartns {'testSuiteId':  '33', 'testCase': 'Creat_Table_Logical_Part_Compress_Attribute'}",
        "sql/CreateTableAX7.0/DDLGenDisplayAnalyticTables {'testSuiteId':  '33', 'testCase': 'E2E_Tests_Tables_With_ANALYTIC'}",
        "sql/CreateTableAX7.0/DDLGenDisplayIndexes {'testSuiteId':  '33', 'testCase': 'Display_Index'}",
        "sql/CreateTableAX7.0/DDLGenDBTables {'testSuiteId':  '33', 'testCase': 'Generate_Database_Command'}",
        "sql/CreateTableAX7.0/DefaultCompressTest {'testSuiteId':  '33', 'testCase': 'Create_Fact_Dimension_Table_DDL_Compress_Attribute'}",
        "sql/CreateTableAX7.0/LowCompressTest {'testSuiteId':  '33', 'testCase': 'Create_Index_Compress_Attribute'}",
        "sql/CreateTableAX7.0/DeprecatedCompressTest {'testSuiteId':  '33', 'testCase': 'Alter_Table_Change_Compress_Level'}",
        "sql/CreateTableAX7.0/CtasTest {'testSuiteId':  '33', 'testCase': 'CTAS_Storage_Compress_Attribute'}",
        "sql/CreateTableAX7.0/AlterTest {'testSuiteId':  '33', 'testCase': 'Alter_Table_Change_Storage_Type'}",
        "sql/CreateTableAX7.0/MetadataSystemViewsList {'testSuiteId':  '33', 'testCase': 'Data_Dictionary_Views_DDL'}",
        "sql/CreateTableAX7.0/MetadataSystemTablesTest {'testSuiteId':  '33', 'testCase': 'Table_Related_Data_Dictionary_Views'}",
        "sql/CreateTableAX7.0/nc_relationstats_test {'testSuiteId':  '33', 'testCase': 'Nc_Relationstats'}",
        "sql/CreateTableAX7.0/NegativeAnalyticTableTest {'testSuiteId':  '33', 'testCase': 'Analytic_Table_Negative_Test'}",
        "sql/CreateTableAX7.0/TempTableTest {'testSuiteId':  '33', 'testCase': 'E2E_Tests_Tables_With_TEMP'}",
        "sql/CreateTableAX7.0/ColumnarTempTableTest {'testSuiteId':  '33', 'testCase': 'Columnar_Temp_Table'}",
        "sql/CreateTableAX7.0/ReactDescribeTest {'testSuiteId':  '33', 'testCase': 'Table_Persistence'}",
        "sql/CreateTableAX7.0/ReactHelpTest {'testSuiteId':  '33', 'testCase': 'ACT_Help_Command_Test'}"
    ],

    "ComponentRemoval" : [
        "devops_installer/ComponentRemoval/VerifyIointerceptorMount {'testSuiteId':  '41', 'testCase' : 'VerifyIointerceptorMount'}",
        "devops_installer/ComponentRemoval/VerifyIOIProcesses {'testSuiteId':  '41', 'testCase' : 'VerifyIOIProcesses'}",
        "devops_installer/ComponentRemoval/VerifyIOIFiles {'testSuiteId':  '41', 'testCase' : 'VerifyIOIFiles'}",
        "devops_installer/ComponentRemoval/VerifyCompressKeyword {'testSuiteId':  '41', 'testCase' : 'VerifyCompressKeyword'}",
        "devops_installer/ComponentRemoval/VerifyAfsProcesses {'testSuiteId':  '439', 'testCase' : 'VerifyAfsProcesses'}",
        "devops_installer/ComponentRemoval/VerifyAfsFiles {'testSuiteId':  '439', 'testCase' : 'VerifyAfsFiles'}",
        "devops_installer/ComponentRemoval/VerifyAfsConnector {'testSuiteId':  '439', 'testCase' : 'VerifyAfsConnector'}",
        "devops_installer/ComponentRemoval/VerifyAfsCommands {'testSuiteId':  '439', 'testCase' : 'VerifyAfsCommands'}",
        "devops_installer/ComponentRemoval/VerifyInstallerShimProcesses {'testSuiteId':  '440', 'testCase' : 'VerifyInstallerShimProcesses'}",
        "devops_installer/ComponentRemoval/VerifyInstallerShimFiles {'testSuiteId':  '440', 'testCase' : 'VerifyInstallerShimFiles'}",
        "devops_installer/ComponentRemoval/VerifyBackupProcesses {'testSuiteId': '543', 'testCase' : 'VerifyBackupProcesses'}",
        "devops_installer/ComponentRemoval/VerifyBackupFiles {'testSuiteId': '543', 'testCase' : 'VerifyBackupFiles'}",
        "devops_installer/ComponentRemoval/VerifyLoaderAdd {'testSuiteId': '1482', 'testCase' : 'VerifyLoaderAdd'}"
    ],
    "MDPersist" : [
         "devops_installer/MDPersistence/ACL/ACLCreateDatabaseAsDBA {'testSuiteId':  '2297', 'testCase' : 'ACL_Create_Database_As_DBA' }",
         "devops_installer/MDPersistence/ACL/ACLCreateDatabaseAsNonDBA {'testSuiteId':  '2297', 'testCase' : 'ACL_Create_Database_As_Non_DBA' } ",
         "devops_installer/MDPersistence/ACL/ACLCreateUserAsDBA {'testSuiteId':  '2297', 'testCase' : 'ACL_Create_User_As_DBA' } ",
         "devops_installer/MDPersistence/ACL/ACLCreateUserAsNonDBA {'testSuiteId':  '2297', 'testCase' : 'ACL_Create_User_As_Non_DBA' } ",
         "devops_installer/MDPersistence/ACL/ACLCreateSchemaAsDBA  {'testSuiteId':  '2297', 'testCase' : 'ACL_Create_Schema_As_DBA' } ",
         "devops_installer/MDPersistence/ACL/ACLCreateSchemaAsNonDBA  {'testSuiteId':  '2297', 'testCase' : 'ACL_Create_Schema_As_Non_DBA' } ",
         "devops_installer/MDPersistence/ACL/ACLCreateForeignServerAsDBA {'testSuiteId':  '2297', 'testCase' : 'ACL_Create_Foreign_Server_As_DBA' } ",
         "devops_installer/MDPersistence/ACL/ACLCreateForeignServerAsNonDBA {'testSuiteId':  '2297', 'testCase' : 'ACL_Create_Foreign_Server_As_Non_DBA' }  ",
         "devops_installer/MDPersistence/ACL/ACLCreateRoleAsDBA {'testSuiteId':  '2297', 'testCase' : 'ACL_Create_Role_As_DBA' } ",
         "devops_installer/MDPersistence/ACL/ACLCreateRoleAsNonDBA  {'testSuiteId':  '2297', 'testCase' : 'ACL_Create_Role_As_Non_DBA' } ",
         "devops_installer/MDPersistence/ACL/ACLAlterUserAsDBA {'testSuiteId':  '2297', 'testCase' : 'ACL_Alter_User_As_DBA' }",
         "devops_installer/MDPersistence/ACL/ACLAlterUserAsNonDBA {'testSuiteId':  '2297', 'testCase' : 'ACL_Alter_User_As_Non_DBA' }",
         "devops_installer/MDPersistence/ACL/ACLGrantCreateOnDatabase {'testSuiteId':  '2297', 'testCase' : 'ACL_Grant_Create_On_Database' }",
         "devops_installer/MDPersistence/ACL/ACLRevokeCreateOnDatabase {'testSuiteId':  '2297', 'testCase' : 'ACL_Revoke_Create_On_Database' }",
         "devops_installer/MDPersistence/ACL/ACLGrantAllOnDatabase {'testSuiteId':  '2297', 'testCase' : 'ACL_Grant_All_On_Database' }",
         "devops_installer/MDPersistence/ACL/ACLGrantAllOnSchema {'testSuiteId':  '2297', 'testCase' : 'ACL_Grant_All_On_Schema' }",
         "devops_installer/MDPersistence/ACL/ACLGrantUsageOnSchema {'testSuiteId':  '2297', 'testCase' : 'ACL_Grant_Usage_On_Schema' }",
         "devops_installer/MDPersistence/ACL/ACLGrantAllOnForeignServer {'testSuiteId':  '2297', 'testCase' : 'ACL_Grant_All_On_Foreign_Server' }",
         "devops_installer/MDPersistence/ACL/ACLGrantUsageOnForeignServer {'testSuiteId':  '2297', 'testCase' : 'ACL_Grant_Usage_On_Foreign_Server' }",
         "devops_installer/MDPersistence/DDL/DDLCreateDatabase {'testSuiteId':  '2421', 'testCase' : 'DDL_Create_Database' }",
         "devops_installer/MDPersistence/DDL/DDLCreateUser {'testSuiteId':  '2421', 'testCase' : 'DDL_Create_User' }",
         "devops_installer/MDPersistence/DDL/DDLCreateSchema {'testSuiteId':  '2421', 'testCase' : 'DDL_Create_Schema' }",
         "devops_installer/MDPersistence/DDL/DDLCreateRole {'testSuiteId':  '2421', 'testCase' : 'DDL_Create_Role' }",
         "devops_installer/MDPersistence/DDL/DDLCreateForeignServer {'testSuiteId':  '2421', 'testCase' : 'DDL_Create_Foreign_Server' }",
         "devops_installer/MDPersistence/DDL/DDLCreateDatabasePrivs01 {'testSuiteId':  '2421', 'testCase' : 'DDL_Create_Database_Privs01' }"
            ],
    
    "SQLH": [
          "connector/load_from_hcat_planner_change/LoadFromHCatalogTextFileJoinTests {'testSuiteId':  '31', 'testCase' : 'Load_From_HCatalog_JoinTests_Query_Plan'}",
          "connector/load_from_hcat_planner_change/LoadFromHCatalogTextFileOuterJoinTests {'testSuiteId':  '31', 'testCase' : 'Load_From_HCatalog_OuterJoinTests_Query_Plan'}",
          "connector/load_from_hcat_planner_change/LoadFromHCatalogJoinTestsUsingFS {'testSuiteId':  '31', 'testCase' : 'Load_From_HCatalog_Using_Foreign_Server_Query_Plan'}",
          "connector/load_from_hcat_planner_change/LoadFromHCatalogDimensionalThresholdTest {'testSuiteId':  '31', 'testCase' : 'loadFromHCatalogDimensionalThreshold_value_test'}",
          "connector/load_from_hcat_planner_change/LoadFromHCatalogCTASAndIISWithJoinTests {'testSuiteId':  '31', 'testCase' : 'Load_From_HCatalog_Used_in_CTAS_IIS_test_plan'}",
          "connector/load_from_hcat_planner_change/LoadFromHCatJoinTblNoStatsTests {'testSuiteId':  '31', 'testCase' : 'Load_From_HCatalog_Join_Tables_with_NoStats_Query_Plan'}",
          "connector/load_from_hcat_planner_change/LoadFromHCatJoinInSubqueryTests {'testSuiteId':  '31', 'testCase' : 'LoadFromHCatalog_In_Subquery_Query_Plan'}",
          "connector/load_from_hcat_planner_change/DefaultLoadFromHCatalogDimensionalThresholdTest {'testSuiteId':  '31', 'testCase' : 'loadFromHCatalogDimensionalThreshold_default_value'}"
     ],

    "PortMapper": [
        "clusterservices/PortConfigurationManagement/PythonApiTest {'testSuiteId':  '1337', 'testCase' : 'getPort()_AllTestCases_for_NightlyRun'}"
    ]
}
