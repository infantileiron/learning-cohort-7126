/** @typedef {{id:number,code:string,learner:string,occurred_at:string,course:string,note:string}} Event */
/** @typedef {{id:number,name:string,start_week:string,end_week:string,as_of:string,horizon:number,known_at:string,state:string,result:object}} Cohort */
/** @typedef {{id:number,cohort_id:number,cohort_week:string,week_index:number,members:string[],attributions:Object<string,string|null>,note:string,status:string}} Intervention */
/** @typedef {{id:number,learner:string,department:string,valid_from:string,valid_to:string|null,registered_at:string,correction_id:number|null,note:string}} DepartmentAssignment */
/** @typedef {{id:number,learner:string,department:string,valid_from:string,valid_to:string|null,registered_at:string,status:string,transfers:Transfer[]}} Correction */
/** @typedef {{id:number,correction_id:number,intervention_id:number,learner:string,from_department:string|null,to_department:string|null,created:string}} Transfer */
