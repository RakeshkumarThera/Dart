{
	"TempSpaceMonitoring" : [
	 "devops_installer/TempSpaceMonitoring/ZeroConThresholdQueen {'testSuiteId':  '30', 'testCase' : 'Zero_Concurrency_Threshold_QueenDb'}",
	"devops_installer/TempSpaceMonitoring/ZeroConThresholdVWorkers  {'testSuiteId':  '30', 'testCase' : 'Zero_Concurrency_Threshold_VWorkers'}",
        "devops_installer/TempSpaceMonitoring/CancelQueryThresholdQueen  {'testSuiteId':  '30', 'testCase' : 'Cancel_Query_Threshold_QueenDb'}",
        "devops_installer/TempSpaceMonitoring/CancelQueryThresholdVWorkers  {'testSuiteId':  '30', 'testCase' : 'Cancel_Query_Threshold_Vworkers'}",
        "devops_installer/TempSpaceMonitoring/KillSessionThresholdQueen  {'testSuiteId':  '30', 'testCase' : 'Kill_Session_Threshold_QueenDb'}",
        "devops_installer/TempSpaceMonitoring/KillSessionThresholdVWorkers  {'testSuiteId':  '30', 'testCase' : 'Kill_Session_Threshold_Vworkers'}",
        "devops_installer/TempSpaceMonitoring/ZeroConThresholdResetWithSpace  {'testSuiteId':  '30', 'testCase' : 'Zero_Concurrency_Threshold_Trigger_Reset'}",
        "devops_installer/TempSpaceMonitoring/ZeroConTriggerQuotaChange  {'testSuiteId':  '30', 'testCase' : 'QoS_Change_Quota_size'}",
        "devops_installer/TempSpaceMonitoring/ZeroConTriggerEnabledChange  {'testSuiteId':  '30', 'testCase' : 'Monitoring_Disabled'}",
        "devops_installer/TempSpaceMonitoring/MultiThresholdQueen  {'testSuiteId':  '30', 'testCase' : 'Multi_threshold_trigger'}",
        "devops_installer/TempSpaceMonitoring/NcliCommandSetConfig  {'testSuiteId':  '30', 'testCase' : 'Ncli_Showconfig'}",
        "devops_installer/TempSpaceMonitoring/NcliCommandCheckConfig  {'testSuiteId':  '30', 'testCase' : 'Ncli_Checkconfig'}"
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

    "YarnFailover": [
        "devops_installer/Yarn/FailoverTests/Failover_InsideYarnContainer {'testSuiteId':  '252', 'testCase' : 'Test01 Cluster_Failure_In_YARN_Container'}",
        "devops_installer/Yarn/FailoverTests/Failover_OutsideYarnContainer {'testSuiteId':  '252', 'testCase' : 'Test02 Cluster_Failure_Outside_YARN_Container'}",
        "devops_installer/Yarn/FailoverTests/Failover_AppMaster {'testSuiteId':  '252', 'testCase' : 'Test06 Application_Master_Failure'}",
        "devops_installer/Yarn/FailoverTests/Failover_NodeManager {'testSuiteId':  '252', 'testCase' : 'Test08 NodeManager_Failover_Impact'}"
    ],

    "AmSysmanComm": [
        "devops_installer/Yarn/AmSysmanCommTests/AmSysmanComm {'testSuiteId':  '222', 'testCase' : 'registerAppMaster'}"
    ],

    "MiscellaneousTests": [
        "devops_installer/Yarn/MiscellaneousTests/StandardEnvironmentTest {'testSuiteId':  '37', 'testCase' : 'YARN_Load_Data_and_Tables'}"
    ],

    "YarnContainerTests": [
        "devops_installer/Yarn/YarnContainerTests/YarnContainerTestSqlmr {'testSuiteId':  '221', 'testCase' : 'Java_SQLMR_Function'}"
    ],

    "NcliSoftOperationTests": [
        "devops_installer/Yarn/NcliSoftOperationTests/NcliSoftRestartTest {'testSuiteId':  '37', 'testCase' : 'NCLI SYSTEM SOFTRESTART', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/NcliSoftOperationTests/NcliSoftShutdownTest {'testSuiteId':  '37', 'testCase' : 'NCLI SYSTEM SOFTSHUTDOWN', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/NcliSoftOperationTests/NcliSoftStartupTest {'testSuiteId':  '37', 'testCase' : 'NCLI SYSTEM SOFTSTARTUP', 'clusterState': 'NOCHECK'}"
    ],

    "AsterYarnConfig": [
        "devops_installer/Yarn/AsterYarnConfigTests/AppMasterJarParamTest {'testSuiteId':  '1684', 'testCase' : 'Test_Path_For_AppMasterJar_Location', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/AsterYarnConfigTests/AppMasterRetryCountParamTest {'testSuiteId':  '1687', 'testCase' : 'Test_Default_Retry_Count', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/AsterYarnConfigTests/AsterYarnServicePortParamTest {'testSuiteId':  '1660', 'testCase' : 'AsterYarnServicePortParamTest', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/AsterYarnConfigTests/ContainerAllocTimeoutMinsParamTest {'testSuiteId':  '1685', 'testCase' : 'Test_Default_Timeout', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/AsterYarnConfigTests/ContainerMemoryInMBParamTest {'testSuiteId':  '1686', 'testCase' : 'Tes_ContainerMemoryInMB_Argument', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/AsterYarnConfigTests/ContainerVCoreParamTest {'testSuiteId':  '1686', 'testCase' : 'Test_ContainerVCores_Argument', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/AsterYarnConfigTests/InstanceNameParamTest {'testSuiteId':  '1676', 'testCase' : 'Test_ClusterName_Argument', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/AsterYarnConfigTests/QueenNodeParamTest {'testSuiteId':  '1683', 'testCase' : 'Test_Valid_Values_For_Queen_Node', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/AsterYarnConfigTests/QueueParamTest {'testSuiteId':  '1804', 'testCase' : 'Valid Yarn queue', 'clusterState': 'NOCHECK'}"
    ],

    "AsteryarnCommand" : [
        "devops_installer/Yarn/AsteryarnCommandTests/TestListInstance1 {'testSuiteId':  '1661', 'testCase' : 'LIST_INSTANCES', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/AsteryarnCommandTests/TestStartInstance {'testSuiteId':  '1661', 'testCase' : 'START_INSTANCE_And_STATUS_INSTANCE', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/AsteryarnCommandTests/TestStopInstance {'testSuiteId':  '1661', 'testCase' : 'STOP_INSTANCE_And_STATUS_INSTANCE', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/AsteryarnCommandTests/YarnSanityTest {'testSuiteId':  '1661', 'testCase' : 'START_INSTANCE+STOP_INSTANCE_Multiple_Times', 'clusterState': 'NOCHECK'}",
        "devops_installer/Yarn/AsteryarnCommandTests/YarnListInstanceTest {'testSuiteId':  '1661', 'testCase' : 'Start_Stop_Cluster', 'clusterState': 'NOCHECK'}"
    ]
}
