import EmailPasswordNode from "supertokens-node/recipe/emailpassword";
import SessionNode from "supertokens-node/recipe/session";
import Dashboard from "supertokens-node/recipe/dashboard";
import { appInfo } from "./appInfo";
import { AuthConfig } from "../interfaces";

export let backendConfig = (): AuthConfig => {
    return {
        framework: "express",
        supertokens: {
            // this is the location of the SuperTokens core.
            connectionURI: "https://try.supertokens.com",
        },
        appInfo,
        // recipeList contains all the modules that you want to
        // use from SuperTokens. See the full list here: https://supertokens.com/docs/guides
        recipeList: [EmailPasswordNode.init(
            {
                signUpFeature: {
                    formFields: [{
                        id: "name",
                        //label: "Full name",
                        //placeholder: "First name and last name"
                    }, {
                        id: "age",
                        //label: "Your age",
                        //placeholder: "How old are you?",
                    }, {
                        id: "country",
                        //label: "Your country",
                        //placeholder: "Where do you live?",
                        optional: true
                    }]
                }

            }
        ), SessionNode.init(), Dashboard.init()],
        isInServerlessEnv: true,
    };
};
